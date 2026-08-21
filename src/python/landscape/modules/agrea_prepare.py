"""Preparazione dei dati AGREA: dall'archivio pubblico al GeoParquet servibile.

Segue la convenzione che il monorepo usa gia': in git ci va solo cio' che e'
piccolo e stabile, e i dati grossi si scaricano dalla fonte a runtime nel volume.
Peronospora fa lo stesso con i GRIB di ECMWF (bucket S3 `ecmwf-data-forecast`,
cartelle `weather/cache/` e `weather/temp_grib/` gitignorate); bollettini con
`data/input_bollettini/` e `data/cache/`.

Differenza di frequenza: peronospora scarica ogni giorno, questo UNA VOLTA
L'ANNO, perche' AGREA pubblica una campagna per anno.

Produce tre file in `paths.AGREA_DIR`:

  agrea<anno>_colture_er.parquet   layer del PAESAGGIO: superficie agricola
      dichiarata piu' il bosco, dissolta per appezzamento, poligoni >= 0,05 ha,
      geometrie semplificate a 1 m. Serve a dire cosa c'e' intorno, non a
      disegnare un bordo.
  agrea<anno>_parcelle_er.parquet  layer del DISEGNO DEL CAMPO: gli stessi dati
      alla granularita' minima esistente (frammento = appezzamento intersecato la
      particella catastale), >= 0,25 ha, NON dissolti e NON semplificati, con la
      chiave `app_id` che dice quali pezzi formano lo stesso campo dichiarato.
  agrea<anno>_elementi_er.parquet  elementi caratteristici del paesaggio (siepi,
      margini, fossi, maceri) come CENTROIDE piu' superficie: servono solo al
      numero aggregato e non si servono mai come geometria al client.

Le due granularita' non sono un doppione: la prima risponde a "quanto pero c'e'
intorno", la seconda a "qual e' esattamente il bordo di questo pezzo". Misurato a
Ferrara: 375.303 frammenti diventano 196.972 appezzamenti, e nessuno degli
appezzamenti contiene due colture diverse.

Scelte misurate, da non cambiare a occhio:
  - `simplify(1 m)`: fa risparmiare il 57% dei byte. Il costo vero, misurato con la
    differenza simmetrica e non con la variazione netta di superficie (che
    compensa gli scostamenti e vale un ingannevole -0,05%): lo 0,4% dell'area sul
    poligono mediano, fino al 7,8% nel caso peggiore, con il bordo spostato di
    0,60 m in mediana e 1,62 m al massimo. Da tenere presente ovunque questa
    geometria venga riusata.
    Per confronto, l'incertezza di posizionamento assoluto e' piu' grande e non
    dipende da noi: la migliore trasformazione da Monte Mario (EPSG:3003) a WGS 84
    disponibile in PROJ dichiara 4 m di accuratezza. Verificato che geopandas usi
    quella e non una peggiore (le altre divergono di 19 e 77 m), e verificato per
    correlazione incrociata contro iColt che non ci sia disallineamento
    sistematico: l'ottimo di sovrapposizione e' a 3 m dallo zero con un guadagno
    dello 0,10%, cioe' rumore.
  - arrotondamento a 6 decimali e NON oltre: a 5 decimali si perde il 3,1% dei
    poligoni, a 4 un terzo, perche' annichila gli elementi lineari.
  - ordinamento Hilbert e `row_group_size=10.000`: e' cio' che rende efficace
    l'indice bbox, e quindi la lettura per finestra invece della cache in memoria
    (681 MB di RSS contro 5.983).
  - NON dissolvere per classe: le query passerebbero da 102 ms a 48 secondi.
"""

import json
import os
import re
import shutil
import tempfile
import time
import urllib.request
from typing import Dict, List, Optional

import geopandas as gpd
import pandas as pd
import shapely
from landscape import paths
from landscape.modules import config

BASE_URL = "https://agreagestione.regione.emilia-romagna.it/agrea-file/UtilizziGrafici"
PROVINCE = ["PC", "PR", "RE", "MO", "BO", "FE", "RA", "FC", "RN"]
# Il file XX contiene particelle FUORI regione (PS, RO, FI, AR, MN...): va escluso.

MIN_HA = 0.05
SIMPLIFY_M = 1.0
PRECISION_DEG = 1e-6
ROW_GROUP = 10_000
# Soglia del layer fine: sotto questa misura il frammento e' una scheggia
# catastale. Vive in config.py perche' la dichiara anche l'API.
PIECE_MIN_HA = config.AGREA_PIECE_MIN_HA

# Macrousi che NON sono coltura: fuori dal denominatore delle percentuali.
MACRO_NON_CROP = {"480", "780", "840", "880", "920"}

MACRO_FAMILY = {
    # permanenti: la linea agronomica fondamentale e' permanente contro annuale
    "160": config.FAMILY_PERMANENT,
    "200": config.FAMILY_PERMANENT,
    "210": config.FAMILY_PERMANENT,
    "220": config.FAMILY_PERMANENT,
    "240": config.FAMILY_PERMANENT,
    "280": config.FAMILY_PERMANENT,
    "320": config.FAMILY_PERMANENT,
    "360": config.FAMILY_PERMANENT,
    "400": config.FAMILY_PERMANENT,
    "120": config.FAMILY_PERMANENT,
    "100": config.FAMILY_PERMANENT,
    "060": config.FAMILY_PERMANENT,
    "440": config.FAMILY_PERMANENT,
    "740": config.FAMILY_PERMANENT,
    # erbacee: tutto cio' che ruota
    "040": config.FAMILY_ANNUAL,
    "070": config.FAMILY_ANNUAL,
    "080": config.FAMILY_ANNUAL,
    "560": config.FAMILY_ANNUAL,
    "600": config.FAMILY_ANNUAL,
    "640": config.FAMILY_ANNUAL,
    "680": config.FAMILY_ANNUAL,
    "720": config.FAMILY_ANNUAL,
    "721": config.FAMILY_ANNUAL,
    "722": config.FAMILY_ANNUAL,
    # semi-naturale: il verde va qui e non ai prati, perche' e' la variabile che
    # la letteratura collega a Halyomorpha halys e Drosophila suzukii
    "480": config.FAMILY_SEMINATURAL,
    "780": config.FAMILY_SEMINATURAL,
    # non agricolo
    "840": config.FAMILY_OTHER,
    "880": config.FAMILY_OTHER,
    "920": config.FAMILY_OTHER,
}

COLONNE = [
    "COD_AZI",
    "ID_APPEZ",
    "COD_MACRO",
    "FLAG_SAU",
    "COD_BIO",
    "DESC_COLT",
    "DESC_DEST",
    "DESC_USO",
    "DESC_QUAL",
]


def specie(desc_colt, desc_dest, desc_uso, desc_qual) -> str:
    """Nome della specie, per rimozione esatta.

    `DESC_COLT` e' la concatenazione di specie + destinazione + uso + varieta', e
    AGREA fornisce gli altri tre in campi propri: togliendoli resta la specie.
    Nessuna regola a parole chiave, nessuna interpretazione. Verificato su tutti i
    778 codici regionali: 366 specie, zero rimozioni fallite.
    """
    s = str(desc_colt or "")
    for f in (desc_dest, desc_uso, desc_qual):
        if isinstance(f, str) and f.strip():
            s = s.replace(f.strip(), "")
    return re.sub(r"\s+", " ", s).strip(" -,") or "NON SPECIFICATO"


def _arrotonda(gs: gpd.GeoSeries) -> gpd.GeoSeries:
    """set_precision a 6 decimali, con ripiego per-geometria.

    Sull'intero layer solleva TopologyException anche dopo make_valid: qualche
    geometria non ammette il riallineamento topologico, e quelle si trattano in
    modalita' pointwise, che non ricostruisce la topologia.
    """
    try:
        return gpd.GeoSeries(
            shapely.set_precision(gs.values, PRECISION_DEG), index=gs.index, crs=gs.crs
        )
    except Exception:
        fuori = []
        for g in gs.values:
            try:
                fuori.append(shapely.set_precision(g, PRECISION_DEG))
            except Exception:
                fuori.append(shapely.set_precision(g, PRECISION_DEG, mode="pointwise"))
        return gpd.GeoSeries(fuori, index=gs.index, crs=gs.crs)


def scarica(anno: int, prov: str, dest_dir: str, log=print) -> str:
    """Scarica un archivio provinciale, restituisce il percorso locale."""
    nome = f"Uti_Part_PCG_{anno}_{prov}.zip"
    url = f"{BASE_URL}/{anno}/{nome}"
    dest = os.path.join(dest_dir, nome)
    t0 = time.time()
    with urllib.request.urlopen(url, timeout=120) as r, open(dest, "wb") as out:
        shutil.copyfileobj(r, out, length=1024 * 1024)
    mb = os.path.getsize(dest) / 1e6
    log(f"    {prov}: scaricati {mb:,.0f} MB in {time.time()-t0:.0f}s")
    return dest


def etag_remoto(anno: int, prov: str) -> Optional[str]:
    """ETag dell'archivio remoto, per capire se e' cambiato senza scaricarlo."""
    url = f"{BASE_URL}/{anno}/Uti_Part_PCG_{anno}_{prov}.zip"
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.headers.get("ETag")
    except Exception:
        return None


def _lavora_provincia(zip_path: str, prov: str, anno: int, tmp: str, log=print):
    base = os.path.basename(zip_path).replace(".zip", "")
    t0 = time.time()
    g = gpd.read_file(
        f"/vsizip/{zip_path}/{base}.shp", engine="pyogrio", columns=COLONNE
    )
    n0 = len(g)

    g["cls"] = [
        specie(a, b, c, d)
        for a, b, c, d in zip(
            g["DESC_COLT"], g["DESC_DEST"], g["DESC_USO"], g["DESC_QUAL"]
        )
    ]
    g["family"] = g["COD_MACRO"].map(MACRO_FAMILY).fillna(config.FAMILY_OTHER)
    g["is_crop_class"] = ~g["COD_MACRO"].isin(MACRO_NON_CROP)

    g = g.set_crs(3003, allow_override=True).to_crs(config.METRIC_EPSG)
    g["geometry"] = g.geometry.make_valid()
    g = g[g.geometry.notna() & ~g.geometry.is_empty]
    g["ha"] = g.geometry.area / 10_000

    # 1) layer della mappa, dissolto per APPEZZAMENTO
    m = g[((g.FLAG_SAU == "S") | (g.COD_MACRO == "480"))].copy()
    # Le geometrie AGREA sono ritagliate sulle particelle catastali: un campo
    # agronomico e' spezzato in piu' frammenti (mediana 2, fino a 88). AGREA li
    # raggruppa con ID_APPEZ, e dissolvendo per (azienda, appezzamento) si
    # ottiene il confine del CAMPO. Misurato: la mediana passa da 0,39 a 1,18 ha,
    # l'86% degli appezzamenti sopra 1 ha risulta un solo poligono contiguo, e
    # nessun appezzamento contiene due colture diverse.
    # Gli identificativi servono solo qui e NON vengono conservati nel file.
    m = m.dissolve(
        by=["COD_AZI", "ID_APPEZ", "cls", "family", "is_crop_class"], as_index=False
    )
    m["geometry"] = m.geometry.make_valid()
    m = m[m.geometry.notna() & ~m.geometry.is_empty]
    m["ha"] = m.geometry.area / 10_000
    m = m[m.ha >= MIN_HA]
    m["geometry"] = m.geometry.simplify(SIMPLIFY_M, preserve_topology=True).make_valid()
    m = m[m.geometry.notna() & ~m.geometry.is_empty].to_crs(4326)
    m["geometry"] = _arrotonda(m.geometry)
    m = m[m.geometry.notna() & ~m.geometry.is_empty]
    m[
        "bio"
    ] = False  # il biologico si perde nel dissolve: si ricava a parte se servira'
    m = m[["cls", "family", "is_crop_class", "ha", "bio", "geometry"]].reset_index(
        drop=True
    )
    m.to_parquet(os.path.join(tmp, f"colture_{prov}.parquet"))

    # 2) layer fine: i PEZZI, cosi' come stanno nel dato
    # Ne' dissolti ne' semplificati, per due ragioni diverse.
    # Non dissolti: chi disegna il proprio campo deve poter scegliere una
    # porzione, e la particella catastale e' l'unica suddivisione che il dato
    # conosce. Non semplificati: la semplificazione lavora un poligono per volta
    # e aprirebbe i bordi condivisi, rendendo l'unione dei pezzi scelti piena di
    # fessure.
    p = g[((g.FLAG_SAU == "S") | (g.COD_MACRO == "480"))].copy()
    p = p[p.ha >= PIECE_MIN_HA]
    # `app_id` dice quali pezzi formano lo stesso campo dichiarato, e NIENTE
    # altro: e' un progressivo locale, non una funzione di COD_AZI. Va cosi'
    # perche' un identificativo derivabile da COD_AZI permetterebbe di
    # raggruppare tutti i terreni di un'azienda, che e' proprio cio' che non
    # dobbiamo servire. Viene poi rinumerato in ordine spaziale in `_unisci`,
    # cosi' che due id vicini siano campi vicini e non campi della stessa
    # azienda.
    chiave = p["COD_AZI"].astype(str) + "|" + p["ID_APPEZ"].astype(str)
    p["app_id"] = prov + "-" + pd.factorize(chiave)[0].astype(str)
    p = p.to_crs(4326)
    # Nessun arrotondamento delle coordinate, al contrario del layer del
    # paesaggio. Li' i 6 decimali fanno risparmiare byte su un dato che deve solo
    # indicare cosa c'e' intorno; qui costano troppo e minacciano proprio la
    # proprieta' che serve. Misurato su Ferrara: `set_precision` in modalita'
    # `valid_output` riallinea la topologia una geometria per volta e aprirebbe i
    # bordi condivisi; in modalita' `pointwise` li conserva, ma degenera 6.057
    # pezzi su 97.758 (6,2%) in GeometryCollection irrecuperabili. Senza
    # arrotondare si perdono 4 pezzi su 97.758 e il file passa da 24,7 a 33,6 MB
    # per provincia: nove megabyte per non far sparire il 6% dei campi
    # selezionabili.
    prima_del_filtro = len(p)
    p = p[p.geometry.notna() & ~p.geometry.is_empty]
    p = p[p.geometry.geom_type.isin(("Polygon", "MultiPolygon"))]
    scartati = prima_del_filtro - len(p)
    p = p[["cls", "family", "is_crop_class", "ha", "app_id", "geometry"]].reset_index(
        drop=True
    )
    p.to_parquet(os.path.join(tmp, f"parcelle_{prov}.parquet"))

    # 3) elementi del paesaggio, come centroide
    e = g[g.COD_MACRO == "780"].copy()
    e["geometry"] = e.geometry.centroid
    e = e.to_crs(4326)
    e = e[e.geometry.notna() & ~e.geometry.is_empty]
    e = e[["cls", "ha", "geometry"]].reset_index(drop=True)
    e.to_parquet(os.path.join(tmp, f"elementi_{prov}.parquet"))

    log(
        f"    {prov}: {n0:,} record -> colture {len(m):,} ({m.ha.sum():,.0f} ha) · "
        f"pezzi {len(p):,} ({p.ha.sum():,.0f} ha, {scartati} scartati) · "
        f"elementi {len(e):,} ({e.ha.sum():,.0f} ha)  in {time.time()-t0:.0f}s"
    )
    del g, m, p, e


def _unisci(
    nome: str, tmp: str, dest_finale: str, log=print, pezzi: bool = False
) -> Dict:
    import glob

    files = sorted(glob.glob(os.path.join(tmp, f"{nome}_*.parquet")))
    d = gpd.GeoDataFrame(
        pd.concat([gpd.read_parquet(f) for f in files], ignore_index=True), crs=4326
    )
    # L'ordinamento Hilbert e' cio' che rende efficace l'indice bbox.
    d = d.iloc[d.geometry.hilbert_distance(level=16).argsort()].reset_index(drop=True)
    if pezzi:
        # Rinumerazione DOPO l'ordinamento spaziale: `app_id` diventa un
        # progressivo in ordine di prima comparsa lungo la curva di Hilbert,
        # quindi due id vicini sono campi geograficamente vicini. Se si
        # rinumerasse prima, l'ordine dell'archivio AGREA e' per azienda e id
        # consecutivi rivelerebbero terreni della stessa azienda.
        d["app_id"] = pd.factorize(d["app_id"])[0].astype("int32")
        # `pid` identifica il singolo pezzo fra una richiesta e l'altra: il
        # frontend ne ha bisogno per ricordare cosa ha selezionato quando la
        # mappa si muove e la sorgente viene ricaricata.
        d["pid"] = pd.RangeIndex(len(d)).astype("int32")
        # Quanti pezzi ha in tutto il campo a cui questo pezzo appartiene. Serve
        # a poter dire "questo campo e' fatto di 4 pezzi, 3 sono nella vista":
        # dalla sola finestra letta non si saprebbe.
        d["app_n"] = d.groupby("app_id")["pid"].transform("size").astype("int16")
    # Scrittura atomica: un'interruzione non deve lasciare un parquet mezzo scritto.
    parziale = dest_finale + ".parziale"
    d.to_parquet(
        parziale, compression="zstd", write_covering_bbox=True, row_group_size=ROW_GROUP
    )
    os.replace(parziale, dest_finale)
    info = {
        "poligoni": int(len(d)),
        "ha": round(float(d["ha"].sum()), 1),
        "mb": round(os.path.getsize(dest_finale) / 1e6, 1),
    }
    if pezzi:
        per_campo = d.groupby("app_id").size()
        info["campi"] = int(len(per_campo))
        info["campi_scomponibili"] = int((per_campo > 1).sum())
    log(
        f"  {nome}: {info['poligoni']:,} poligoni · {info['ha']:,.0f} ha · "
        f"{info['mb']} MB -> {dest_finale}"
    )
    return info


def stato(anno: int) -> Dict:
    """Cosa c'e' sul volume e con quali ETag e' stato prodotto."""
    manifest = paths.AGREA_DIR / f"agrea{anno}_manifest.json"
    out = {
        "anno": anno,
        "colture": paths.AGREA_COLTURE_PARQUET.exists(),
        "parcelle": paths.AGREA_PARCELLE_PARQUET.exists(),
        "elementi": paths.AGREA_ELEMENTI_PARQUET.exists(),
        "manifest": None,
    }
    if manifest.exists():
        try:
            out["manifest"] = json.loads(manifest.read_text())
        except Exception:
            pass
    return out


def aggiorna(
    anno: int = config.AGREA_YEAR,
    province: Optional[List[str]] = None,
    force: bool = False,
    da_cartella: Optional[str] = None,
    log=print,
) -> Dict:
    """Scarica e prepara, solo se serve. Idempotente.

    Se i file esistono e gli ETag remoti combaciano con quelli registrati non fa
    nulla: si puo' invocare a ogni avvio senza costo.

    `da_cartella` usa archivi gia' presenti su disco invece di scaricarli: serve
    in sviluppo per rigenerare senza riscaricare 2 GB. In produzione non si usa.
    """
    province = province or PROVINCE
    manifest_path = paths.AGREA_DIR / f"agrea{anno}_manifest.json"

    etag_locali = {}
    if manifest_path.exists() and not force:
        try:
            etag_locali = json.loads(manifest_path.read_text()).get("etag", {})
        except Exception:
            etag_locali = {}

    completo = (
        paths.AGREA_COLTURE_PARQUET.exists()
        and paths.AGREA_PARCELLE_PARQUET.exists()
        and paths.AGREA_ELEMENTI_PARQUET.exists()
    )
    if completo and not force and not da_cartella:
        log("verifico se gli archivi remoti sono cambiati...")
        etag_remoti = {p: etag_remoto(anno, p) for p in province}
        if etag_locali and all(
            etag_locali.get(p) and etag_locali[p] == etag_remoti.get(p)
            for p in province
        ):
            log("nulla da fare: i dati sul volume corrispondono agli archivi remoti.")
            return {"aggiornato": False, "motivo": "etag invariati"}
        log("gli archivi remoti sono cambiati (o non erano registrati): rigenero.")

    paths.AGREA_DIR.mkdir(parents=True, exist_ok=True)
    etag_usati = {}
    with tempfile.TemporaryDirectory(dir=str(paths.AGREA_DIR)) as tmp:
        log(f"preparazione AGREA {anno}, {len(province)} province")
        for p in province:
            if da_cartella:
                z = os.path.join(da_cartella, f"Uti_Part_PCG_{anno}_{p}.zip")
                if not os.path.exists(z):
                    raise FileNotFoundError(z)
                log(f"    {p}: uso l'archivio locale")
                _lavora_provincia(z, p, anno, tmp, log=log)
            else:
                etag_usati[p] = etag_remoto(anno, p)
                z = scarica(anno, p, tmp, log=log)
                _lavora_provincia(z, p, anno, tmp, log=log)
                # L'archivio si butta subito: 2 GB non restano sul volume.
                os.remove(z)
        log("unisco e scrivo...")
        info_c = _unisci("colture", tmp, str(paths.AGREA_COLTURE_PARQUET), log=log)
        info_p = _unisci(
            "parcelle", tmp, str(paths.AGREA_PARCELLE_PARQUET), log=log, pezzi=True
        )
        info_e = _unisci("elementi", tmp, str(paths.AGREA_ELEMENTI_PARQUET), log=log)

    manifest_path.write_text(
        json.dumps(
            {
                "anno": anno,
                "province": province,
                "etag": etag_usati,
                "colture": info_c,
                "parcelle": info_p,
                "elementi": info_e,
                "prodotto_il": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "fonte": f"{BASE_URL}/{anno}/",
            },
            indent=2,
        )
    )
    return {
        "aggiornato": True,
        "colture": info_c,
        "parcelle": info_p,
        "elementi": info_e,
    }
