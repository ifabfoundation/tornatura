"""Preparazione delle zone semi-naturali: le fonti regionali ed europee, ritagliate fuori da AGREA.

Si esegue dall'updater DOPO AGREA (servono gli appezzamenti e le forme degli elementi) e scrive in
`paths.SEMINATURALE_DIR`:

  strati_er.parquet    Carta forestale regionale 2025 e Uso del suolo di dettaglio 2023, per
      categoria (config.SEMINATURAL_*), in EPSG:32632. Ogni poligono e' gia' ritagliato fuori da
      tutto cio' che viene prima nell'ordine di priorita': la Carta forestale fuori da appezzamenti
      ed elementi AGREA; l'Uso del suolo fuori da AGREA e da QUALSIASI poligono della Carta
      forestale. A richiesta si sommano quindi superfici che non si toccano.
  mappa_er.parquet     gli stessi strati per la sola mappa: uniti per categoria e fonte dentro
      celle di 5 km e semplificati a 5 m (4 volte meno vertici).
  swf_residuo_er.tif   Copernicus Small Woody Features 2021 (5 m, EPSG:3035): 1 dove c'e' una
      siepe o un albero che nessuna delle fonti precedenti vede, 0 altrove.
  manifest.json        versioni delle fonti usate, per non rifare nulla se niente e' cambiato.

Perche' qui e non a richiesta: il ritaglio al volo del solo bosco costava 18 s a 10 km in collina,
fatto una volta sulla regione costa ~12 minuti e poi 0,05 s a richiesta (esperimento
esperimenti/bosco_paesaggio/, 33 punti x 4 raggi). Picco di memoria misurato ~4 GB.

Fonti (tutte pubbliche, CC BY 4.0 o equivalente, da citare):
  - Carta forestale: un archivio per provincia, dal sito Ambiente della Regione;
  - Uso del suolo 2023: un archivio regionale dal geoportale (servizio "packs");
  - Small Woody Features: servizio immagini pubblico di Copernicus (exportImage), a riquadri.
Se una fonte non risponde, i file vecchi restano validi; se mancano del tutto, il servizio usa il
solo AGREA e lo dichiara.
"""

import json
import os
import shutil
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
from typing import Dict, List, Optional

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from landscape import paths
from landscape.modules import config

CF_URL = (
    "https://ambiente.regione.emilia-romagna.it/it/parchi-natura2000/foreste/"
    "quadro-conoscitivo/sistema-informativo-regionale/carta-forestale-regionale/"
    "cartaforestale{prov}.zip/@@download/file"
)
CF_PROVINCE = ["pc", "pr", "re", "mo", "bo", "fe", "ra", "fc", "rn"]
# Uso del suolo di dettaglio 2023, EPSG:7791 (RDN2008 / UTM 32N). Il servizio non da' ETag: la
# versione e' l'edizione (2023), che non cambia; una nuova edizione e' un nuovo indirizzo.
US_URL = "https://servizimoka.regione.emilia-romagna.it/download/api/packs?p=3181"
US_EDIZIONE = "uso_suolo_dettaglio_2023_epsg7791"
SWF_URL = (
    "https://copernicus.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/"
    "HRL_SmallWoodyFeatures_2021/ImageServer/exportImage?"
)
SWF_PIXEL_M = 5
SWF_EPSG = 3035
# Riquadri entro i limiti del servizio (maxImageWidth 15000, maxImageHeight 4100).
SWF_TILE_W, SWF_TILE_H = 15000, 4100
# Lato dei riquadri del ritaglio vettoriale (EPSG:32632): abbastanza piccoli da leggere poco
# AGREA per volta, abbastanza grandi da non rileggere troppe volte gli stessi appezzamenti.
RIQUADRO_M = 10_000


def _scarica(url: str, dest: str, log=print, tentativi: int = 4) -> str:
    for t in range(tentativi):
        try:
            t0 = time.time()
            with urllib.request.urlopen(url, timeout=600) as r, open(dest, "wb") as out:
                shutil.copyfileobj(r, out, length=1024 * 1024)
            log(
                f"    scaricato {os.path.basename(dest)}: {os.path.getsize(dest) / 1e6:,.0f} MB "
                f"in {time.time() - t0:.0f}s"
            )
            return dest
        except Exception as exc:
            if t == tentativi - 1:
                raise
            log(f"    tentativo {t + 1} fallito ({exc}), riprovo")
            time.sleep(10 * (t + 1))
    return dest


def _versione_cf(prov: str) -> Optional[str]:
    """Data e dimensione dell'archivio remoto: il sito non da' ETag."""
    req = urllib.request.Request(CF_URL.format(prov=prov), method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return f"{r.headers.get('Last-Modified')}|{r.headers.get('Content-Length')}"
    except Exception:
        return None


def _shp_nello_zip(zip_path: str) -> str:
    with zipfile.ZipFile(zip_path) as z:
        nomi = [n for n in z.namelist() if n.lower().endswith(".shp")]
    if len(nomi) != 1:
        raise ValueError(f"{zip_path}: attesi uno shapefile, trovati {nomi}")
    return f"/vsizip/{zip_path}/{nomi[0]}"


def sottrai(cand: gpd.GeoDataFrame, occ: gpd.GeoSeries, log=print) -> gpd.GeoDataFrame:
    """Ogni poligono candidato MENO l'unione dei poligoni occupati che lo toccano.

    Poligono per poligono con l'indice spaziale, non un'unica unione regionale: l'unione di
    1,7 milioni di appezzamenti ed elementi non sta in memoria in modo utile.
    """
    i_c, i_o = occ.sindex.query(cand.geometry, predicate="intersects")
    geo = cand.geometry.values.copy()
    occ_v = occ.values
    if len(i_c):
        ordine = np.argsort(i_c, kind="stable")
        i_c, i_o = i_c[ordine], i_o[ordine]
        confini = np.flatnonzero(np.diff(i_c)) + 1
        for k, (bc, bo) in enumerate(
            zip(np.split(i_c, confini), np.split(i_o, confini))
        ):
            geo[bc[0]] = shapely.difference(geo[bc[0]], shapely.union_all(occ_v[bo]))
            if k and k % 50000 == 0:
                log(f"    {k:,} poligoni ritagliati")
    out = gpd.GeoDataFrame(cand.drop(columns="geometry"), geometry=geo, crs=cand.crs)
    out = out[~out.geometry.isna() & ~out.geometry.is_empty]
    out["geometry"] = out.geometry.make_valid()
    # la differenza lascia a volte linee o punti di bordo: si tiene solo la parte areale
    out["geometry"] = [
        shapely.union_all([p for p in shapely.get_parts(g) if p.area > 0])
        if g.geom_type == "GeometryCollection"
        else g
        for g in out.geometry.values
    ]
    return out[
        ~out.geometry.isna() & ~out.geometry.is_empty & (out.geometry.area > 1.0)
    ]


def _agrea_nel_riquadro(bounds_m) -> gpd.GeoSeries:
    """Appezzamenti AGREA (qualunque classe) ed elementi con la forma dentro un riquadro in metri.

    Letti per finestra dai GeoParquet, riquadro per riquadro: tutta la regione insieme (1,7 milioni
    di poligoni con il loro indice) faceva salire l'updater a 11 GB (misurato il 28/09/2026).
    """
    box_m = shapely.box(*bounds_m)
    b_geo = gpd.GeoSeries([box_m], crs=config.METRIC_EPSG).to_crs(4326).total_bounds
    ag = gpd.read_parquet(
        paths.AGREA_COLTURE_PARQUET, columns=["geometry"], bbox=tuple(b_geo)
    ).geometry
    ag = ag.to_crs(config.METRIC_EPSG).make_valid()
    el = gpd.read_parquet(
        paths.AGREA_ELEMENTI_FORME_PARQUET, columns=["geometry"], bbox=tuple(bounds_m)
    ).geometry
    return _unione(ag, el.to_crs(config.METRIC_EPSG))


def _unione(*serie: gpd.GeoSeries) -> gpd.GeoSeries:
    return gpd.GeoSeries(
        pd.concat(list(serie), ignore_index=True), crs=config.METRIC_EPSG
    )


def _griglia(g: gpd.GeoDataFrame) -> pd.Series:
    """Riquadro di appartenenza di ogni poligono (per il punto interno), lato RIQUADRO_M."""
    p = g.geometry.representative_point()
    return (
        (p.x // RIQUADRO_M).astype(int).astype(str)
        + "_"
        + (p.y // RIQUADRO_M).astype(int).astype(str)
    )


def _sottrai_a_riquadri(
    cand: gpd.GeoDataFrame,
    extra: Optional[gpd.GeoSeries],
    log=print,
    cf_pq: Optional[str] = None,
) -> gpd.GeoDataFrame:
    """`sottrai` riquadro per riquadro: per ogni gruppo di candidati si legge solo l'AGREA che
    tocca la loro estensione (piu' `extra` se c'e', piu' la Carta forestale letta per finestra da
    `cf_pq` se c'e')."""
    parti = []
    gruppi = cand.groupby(_griglia(cand))
    for k, (_, gruppo) in enumerate(gruppi):
        occ = _agrea_nel_riquadro(gruppo.total_bounds)
        if extra is not None:
            vicini = extra.iloc[
                extra.sindex.query(
                    shapely.box(*gruppo.total_bounds), predicate="intersects"
                )
            ]
            occ = _unione(occ, vicini)
        if cf_pq is not None:
            vicini = gpd.read_parquet(
                cf_pq, bbox=tuple(gruppo.total_bounds), columns=["geometry"]
            ).geometry
            occ = _unione(occ, vicini)
        parti.append(sottrai(gruppo, occ, log=lambda *_: None) if len(occ) else gruppo)
        if k and k % 100 == 0:
            log(f"    {k:,} riquadri su {gruppi.ngroups:,}")
    return gpd.GeoDataFrame(pd.concat(parti, ignore_index=True), crs=config.METRIC_EPSG)


def _rss_gb() -> float:
    """Memoria residente del processo, in GB (da /proc: nessuna dipendenza in piu')."""
    try:
        with open("/proc/self/status") as f:
            for riga in f:
                if riga.startswith("VmRSS:"):
                    return int(riga.split()[1]) / 1e6
    except OSError:
        pass
    return 0.0


def _scrivi(g: gpd.GeoDataFrame, dest: str) -> None:
    """GeoParquet ordinato per Hilbert con bbox di copertura: si legge per finestra."""
    if len(g):
        g = g.iloc[g.geometry.hilbert_distance(level=16).argsort()]
    g.reset_index(drop=True).to_parquet(
        dest, compression="zstd", write_covering_bbox=True, row_group_size=10_000
    )


def _leggi_parti(files: List[str], bbox=None, columns=None) -> gpd.GeoDataFrame:
    """Unione dei GeoParquet temporanei, letti per finestra se c'e' `bbox`."""
    parti = [gpd.read_parquet(f, bbox=bbox, columns=columns) for f in files]
    parti = [p for p in parti if len(p)]
    if not parti:
        return gpd.GeoDataFrame(
            {c: [] for c in (columns or []) if c != "geometry"},
            geometry=[],
            crs=config.METRIC_EPSG,
        )
    return gpd.GeoDataFrame(pd.concat(parti, ignore_index=True), crs=config.METRIC_EPSG)


US_BLOCCO = 100_000


def _strati(cf_zips: List[str], us_zip: str, tmp: str, log=print) -> List[str]:
    """Strati ritagliati, scritti in `tmp` a pezzi; restituisce i file.

    Scrive anche l'Uso del suolo intero (`us_*.parquet`, per il raster) e la Carta forestale
    intera (`cf.parquet`, per ritagliarle fuori l'Uso del suolo). Nessuna delle due carte resta
    in memoria tutta insieme: l'Uso del suolo si legge a blocchi di 100.000 poligoni.
    """
    cf = gpd.GeoDataFrame(
        pd.concat(
            [
                gpd.read_file(
                    _shp_nello_zip(z), columns=["STC_RER"], engine="pyogrio"
                ).to_crs(config.METRIC_EPSG)
                for z in cf_zips
            ],
            ignore_index=True,
        ),
        geometry="geometry",
        crs=config.METRIC_EPSG,
    )
    cf["STC_RER"] = cf["STC_RER"].astype(str)
    cf["geometry"] = cf.geometry.make_valid()
    cf_pq = os.path.join(tmp, "cf.parquet")
    _scrivi(cf[["geometry"]], cf_pq)
    c = cf[cf["STC_RER"].isin(config.SEMINATURAL_CF_STC)].copy()
    del cf
    c["categoria"] = c["STC_RER"].map(config.SEMINATURAL_CF_STC)
    c["fonte"] = "cf2025"
    c["classe"] = c["STC_RER"]
    log(
        f"  Carta forestale: {len(c):,} poligoni nelle categorie; ritaglio fuori da AGREA"
        f" (memoria {_rss_gb():.1f} GB)"
    )
    c = _sottrai_a_riquadri(
        c[["categoria", "fonte", "classe", "geometry"]], None, log=log
    )
    uscite = [os.path.join(tmp, "strati_cf.parquet")]
    c["ha"] = c.geometry.area / 10_000
    _scrivi(c, uscite[0])
    del c

    shp = _shp_nello_zip(us_zip)
    n = 0
    while True:
        us = gpd.read_file(
            shp,
            columns=["COD_TOT"],
            engine="pyogrio",
            skip_features=n * US_BLOCCO,
            max_features=US_BLOCCO,
        )
        if us.empty:
            break
        us = us.to_crs(config.METRIC_EPSG)
        us["COD_TOT"] = us["COD_TOT"].astype(str)
        us["geometry"] = us.geometry.make_valid()
        # Tutto l'Uso del suolo serve al raster (dove finisce la regione, quali pixel sono vigneti
        # o frutteti): resta in GeoParquet temporanei da leggere per finestra.
        _scrivi(us, os.path.join(tmp, f"us_{n}.parquet"))
        u = us[us["COD_TOT"].isin(config.SEMINATURAL_US_COD)].copy()
        del us
        u["categoria"] = u["COD_TOT"].map(config.SEMINATURAL_US_COD)
        u["fonte"] = "us2023"
        u["classe"] = u["COD_TOT"]
        log(
            f"  Uso del suolo, blocco {n + 1}: {len(u):,} poligoni nelle categorie; ritaglio fuori"
            f" da AGREA e CF (memoria {_rss_gb():.1f} GB)"
        )
        u = _sottrai_a_riquadri(
            u[["categoria", "fonte", "classe", "geometry"]], None, log=log, cf_pq=cf_pq
        )
        uscite.append(os.path.join(tmp, f"strati_us_{n}.parquet"))
        u["ha"] = u.geometry.area / 10_000
        _scrivi(u, uscite[-1])
        del u
        n += 1
    return uscite


def _raster_swf(tmp: str, dest: str, log=print) -> Dict:
    """Il residuo Small Woody Features: pixel di siepi e alberi che nessuna fonte vede.

    A riquadri (i limiti del servizio Copernicus), e per ogni riquadro si leggono per finestra
    solo le geometrie che lo toccano: memoria costante, qualunque sia la regione.
    """
    import glob

    import rasterio
    from rasterio import features
    from rasterio.transform import from_origin
    from rasterio.windows import Window

    us_pq = sorted(glob.glob(os.path.join(tmp, "us_*.parquet")))
    # Estensione: la regione, cioe' dove c'e' l'Uso del suolo (copre tutto e solo l'ER).
    tb = np.array([np.inf, np.inf, -np.inf, -np.inf])
    for f in us_pq:
        b = gpd.read_parquet(f, columns=["geometry"]).total_bounds
        tb = np.array(
            [min(tb[0], b[0]), min(tb[1], b[1]), max(tb[2], b[2]), max(tb[3], b[3])]
        )
    b = (
        gpd.GeoSeries(shapely.box(*tb), crs=config.METRIC_EPSG)
        .to_crs(SWF_EPSG)
        .total_bounds
    )
    x0 = np.floor(b[0] / SWF_PIXEL_M) * SWF_PIXEL_M - 100
    y1 = np.ceil(b[3] / SWF_PIXEL_M) * SWF_PIXEL_M + 100
    larg = int(np.ceil((b[2] + 100 - x0) / SWF_PIXEL_M))
    alt = int(np.ceil((y1 - (b[1] - 100)) / SWF_PIXEL_M))
    profilo = dict(
        driver="GTiff",
        width=larg,
        height=alt,
        count=1,
        dtype="uint8",
        crs=f"EPSG:{SWF_EPSG}",
        transform=from_origin(x0, y1, SWF_PIXEL_M, SWF_PIXEL_M),
        compress="deflate",
        tiled=True,
        blockxsize=512,
        blockysize=512,
        nodata=None,
    )
    parziale = dest + ".parziale"
    tot_swf = tot_res = 0
    n_riq = 0
    with rasterio.open(parziale, "w", **profilo) as out:
        for r0 in range(0, alt, SWF_TILE_H):
            for c0 in range(0, larg, SWF_TILE_W):
                w = min(SWF_TILE_W, larg - c0)
                h = min(SWF_TILE_H, alt - r0)
                tx0 = x0 + c0 * SWF_PIXEL_M
                ty1 = y1 - r0 * SWF_PIXEL_M
                bb = (tx0, ty1 - h * SWF_PIXEL_M, tx0 + w * SWF_PIXEL_M, ty1)
                t_riq = from_origin(tx0, ty1, SWF_PIXEL_M, SWF_PIXEL_M)
                box_m = (
                    gpd.GeoSeries(shapely.box(*bb), crs=SWF_EPSG)
                    .to_crs(config.METRIC_EPSG)
                    .iloc[0]
                )
                us = _leggi_parti(us_pq, bbox=box_m.bounds)
                if us.empty:
                    continue

                def maschera(geoms: gpd.GeoSeries) -> np.ndarray:
                    geoms = geoms[~geoms.isna() & ~geoms.is_empty]
                    if geoms.empty:
                        return np.zeros((h, w), dtype=bool)
                    return features.rasterize(
                        ((x, 1) for x in geoms.to_crs(SWF_EPSG).values),
                        out_shape=(h, w),
                        transform=t_riq,
                        fill=0,
                        dtype="uint8",
                    ).astype(bool)

                q = urllib.parse.urlencode(
                    {
                        "bbox": ",".join(f"{v:.2f}" for v in bb),
                        "bboxSR": SWF_EPSG,
                        "imageSR": SWF_EPSG,
                        "size": f"{w},{h}",
                        "format": "tiff",
                        "pixelType": "U8",
                        "compression": "LZW",
                        "interpolation": "RSP_NearestNeighbor",
                        "f": "image",
                    }
                )
                f_riq = os.path.join(tmp, "swf_riquadro.tif")
                _scarica(SWF_URL + q, f_riq, log=lambda *_: None)
                with open(f_riq, "rb") as fh:
                    if fh.read(2) not in (b"II", b"MM"):
                        raise ValueError(
                            "Small Woody Features: la risposta non e' un TIFF"
                        )
                with rasterio.open(f_riq) as src:
                    swf = src.read(1) == 1
                if swf.shape != (h, w):
                    raise ValueError(
                        f"Small Woody Features: riquadro {swf.shape} invece di {(h, w)}"
                    )

                # Fuori dalla regione non si conta nulla: le altre fonti li' non esistono.
                dentro = maschera(us.geometry)
                # Gia' visti: appezzamenti AGREA, elementi AGREA con un margine per lo scarto di
                # posizione fra le fonti, strati CF/US, colture a filari dell'Uso del suolo.
                b_geo = (
                    gpd.GeoSeries([box_m], crs=config.METRIC_EPSG)
                    .to_crs(4326)
                    .total_bounds
                )
                ag = gpd.read_parquet(
                    paths.AGREA_COLTURE_PARQUET, columns=["geometry"], bbox=tuple(b_geo)
                ).geometry.to_crs(config.METRIC_EPSG)
                coperto = maschera(ag)
                del ag
                el = gpd.read_parquet(
                    paths.AGREA_ELEMENTI_FORME_PARQUET,
                    columns=["geometry"],
                    bbox=box_m.bounds,
                ).geometry
                coperto |= maschera(el.buffer(config.SEMINATURAL_SWF_ELEMENT_MARGIN_M))
                del el
                st = gpd.read_parquet(
                    paths.SEMINATURALE_STRATI_PARQUET,
                    columns=["geometry"],
                    bbox=box_m.bounds,
                ).geometry
                coperto |= maschera(st)
                coperto |= maschera(
                    us.loc[
                        us["COD_TOT"].isin(config.SEMINATURAL_SWF_EXCLUDED_US)
                    ].geometry
                )
                residuo = swf & dentro & ~coperto
                out.write(residuo.astype("uint8"), 1, window=Window(c0, r0, w, h))
                tot_swf += int((swf & dentro).sum())
                tot_res += int(residuo.sum())
                n_riq += 1
                log(
                    f"    riquadro {n_riq}: siepi {int((swf & dentro).sum()) * 25 / 1e4:,.0f} ha, "
                    f"residuo {int(residuo.sum()) * 25 / 1e4:,.0f} ha (memoria {_rss_gb():.1f} GB)"
                )
                del us, st, swf, dentro, coperto, residuo
                time.sleep(0.5)  # gentilezza verso il servizio pubblico
    os.replace(parziale, dest)
    area = SWF_PIXEL_M * SWF_PIXEL_M / 10_000
    return {
        "riquadri": n_riq,
        "swf_ha": round(tot_swf * area, 1),
        "residuo_ha": round(tot_res * area, 1),
        "mb": round(os.path.getsize(dest) / 1e6, 1),
    }


def _unisci_strati(parti: List[str], dest: str) -> Dict:
    """Un solo GeoParquet ordinato per Hilbert, senza caricare le geometrie come oggetti.

    Le tabelle Arrow tengono le geometrie come WKB (byte): unirle e riordinarle costa una frazione
    della memoria di un GeoDataFrame (misurato: 3,8 GB con geopandas per ~400.000 poligoni).
    L'ordine viene dal centro del bbox di copertura, che ogni pezzo ha gia'.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    metadati = pq.read_schema(parti[0]).metadata
    t = pa.concat_tables([pq.read_table(f) for f in parti], promote_options="default")
    bb = t.column("bbox").combine_chunks()
    cx = (np.asarray(bb.field("xmin")) + np.asarray(bb.field("xmax"))) / 2
    cy = (np.asarray(bb.field("ymin")) + np.asarray(bb.field("ymax"))) / 2
    punti = gpd.GeoSeries(gpd.points_from_xy(cx, cy), crs=config.METRIC_EPSG)
    t = t.take(pa.array(np.argsort(punti.hilbert_distance(level=16).values)))
    # i metadati "geo" (CRS, colonna geometria, bbox di copertura) sono quelli dei pezzi, con
    # l'estensione ricalcolata su tutto
    geo = json.loads(metadati[b"geo"])
    geo["columns"]["geometry"]["bbox"] = [
        float(np.min(bb.field("xmin"))),
        float(np.min(bb.field("ymin"))),
        float(np.max(bb.field("xmax"))),
        float(np.max(bb.field("ymax"))),
    ]
    t = t.replace_schema_metadata({**metadati, b"geo": json.dumps(geo).encode()})
    parziale = dest + ".parziale"
    pq.write_table(t, parziale, compression="zstd", row_group_size=10_000)
    os.replace(parziale, dest)
    per_cat = (
        t.select(["categoria", "fonte", "ha"])
        .to_pandas()
        .groupby(["categoria", "fonte"])["ha"]
        .sum()
        .round(0)
    )
    return {"poligoni": t.num_rows, "per_cat": per_cat}


def _mappa(log=print) -> Dict:
    """Lo strato per la mappa: poligoni uniti per categoria e fonte dentro celle di 5 km.

    Cella per cella, leggendo dal file degli strati solo cio' che tocca la cella: tutta la
    regione insieme portava l'updater a 5 GB.
    """
    src = paths.SEMINATURALE_STRATI_PARQUET
    lato = config.SEMINATURAL_MAP_CELL_M
    # l'estensione dalla sola colonna bbox, senza caricare le geometrie
    import pyarrow.parquet as pq

    bb = pq.read_table(src, columns=["bbox"]).column("bbox").combine_chunks()
    x0 = float(np.min(bb.field("xmin")))
    y0 = float(np.min(bb.field("ymin")))
    x1 = float(np.max(bb.field("xmax")))
    y1 = float(np.max(bb.field("ymax")))
    parti = []
    for cx in np.arange(np.floor(x0 / lato) * lato, x1, lato):
        for cy in np.arange(np.floor(y0 / lato) * lato, y1, lato):
            cella = shapely.box(cx, cy, cx + lato, cy + lato)
            dentro = gpd.read_parquet(
                src, bbox=cella.bounds, columns=["categoria", "fonte", "geometry"]
            )
            dentro = dentro[dentro["categoria"].isin(config.SEMINATURAL_MAP_CATEGORIES)]
            if dentro.empty:
                continue
            dentro = dentro.iloc[dentro.sindex.query(cella, predicate="intersects")]
            dentro = dentro.assign(geometry=dentro.geometry.intersection(cella))
            u = dentro.dissolve(by=["categoria", "fonte"], as_index=False)
            u = u.explode(index_parts=False)
            u = u[u.geometry.geom_type == "Polygon"]
            u["geometry"] = u.geometry.simplify(
                config.SEMINATURAL_MAP_SIMPLIFY_M, preserve_topology=True
            )
            parti.append(u[~u.geometry.is_empty & (u.geometry.area > 1.0)])
    m = gpd.GeoDataFrame(pd.concat(parti, ignore_index=True), crs=config.METRIC_EPSG)
    m["ha"] = m.geometry.area / 10_000
    parziale = str(paths.SEMINATURALE_MAPPA_PARQUET) + ".parziale"
    _scrivi(m, parziale)
    os.replace(parziale, paths.SEMINATURALE_MAPPA_PARQUET)
    info = {
        "poligoni": int(len(m)),
        "vertici": int(shapely.get_num_coordinates(m.geometry.values).sum()),
        "mb": round(paths.SEMINATURALE_MAPPA_PARQUET.stat().st_size / 1e6, 1),
    }
    log(
        f"  mappa: {info['poligoni']:,} poligoni, {info['vertici']:,} vertici, {info['mb']} MB"
        f" (memoria {_rss_gb():.1f} GB)"
    )
    return info


def stato() -> Dict:
    out = {
        "strati": paths.SEMINATURALE_STRATI_PARQUET.exists(),
        "swf": paths.SEMINATURALE_SWF_TIF.exists(),
        "mappa": paths.SEMINATURALE_MAPPA_PARQUET.exists(),
        "manifest": None,
    }
    if paths.SEMINATURALE_MANIFEST.exists():
        try:
            out["manifest"] = json.loads(paths.SEMINATURALE_MANIFEST.read_text())
        except Exception:
            pass
    return out


def aggiorna(force: bool = False, da_cartella: Optional[str] = None, log=print) -> Dict:
    """Scarica le fonti e prepara gli strati, solo se serve. Idempotente.

    Serve rifarlo quando cambia AGREA (il ritaglio dipende dagli appezzamenti) o una fonte.
    `da_cartella`: archivi gia' su disco (cartaforestale<prov>.zip, uso_suolo_2023*.zip), per lo
    sviluppo; il raster Copernicus si scarica comunque.
    """
    if not (
        paths.AGREA_COLTURE_PARQUET.exists()
        and paths.AGREA_ELEMENTI_FORME_PARQUET.exists()
    ):
        log(
            "semi-naturale: mancano i file AGREA (appezzamenti e forme degli elementi): salto."
        )
        return {"aggiornato": False, "motivo": "AGREA assente"}
    agrea_man = paths.AGREA_DIR / f"agrea{config.AGREA_YEAR}_manifest.json"
    try:
        agrea_versione = json.loads(agrea_man.read_text()).get("prodotto_il")
    except Exception:
        agrea_versione = None
    versioni = {
        "agrea": agrea_versione,
        "cf2025": {p: _versione_cf(p) for p in CF_PROVINCE}
        if not da_cartella
        else "locale",
        "us2023": US_EDIZIONE,
        "swf2021": "HRL_SmallWoodyFeatures_2021",
        "regole": _impronta_regole(),
    }
    vecchio = stato()
    invariato = (
        not force
        and vecchio["strati"]
        and vecchio["swf"]
        and vecchio["manifest"]
        and vecchio["manifest"].get("versioni") == versioni
    )
    if invariato and vecchio["mappa"]:
        log("semi-naturale: nulla da fare, fonti e AGREA invariati.")
        return {"aggiornato": False, "motivo": "versioni invariate"}
    if invariato:
        # Manca solo lo strato della mappa (volume preparato da una versione precedente):
        # si ricava dagli strati gia' presenti, in un paio di minuti, senza riscaricare nulla.
        manifest = dict(vecchio["manifest"])
        manifest["mappa"] = _mappa(log=log)
        paths.SEMINATURALE_MANIFEST.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False)
        )
        return {"aggiornato": True, "motivo": "solo lo strato della mappa"}

    t0 = time.time()
    paths.SEMINATURALE_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(paths.SEMINATURALE_DIR)) as tmp:
        log("semi-naturale: scarico le fonti")
        cf_zips = []
        for p in CF_PROVINCE:
            if da_cartella:
                z = os.path.join(da_cartella, f"cartaforestale{p}.zip")
                if not os.path.exists(z):
                    raise FileNotFoundError(z)
            else:
                z = _scarica(
                    CF_URL.format(prov=p),
                    os.path.join(tmp, f"cartaforestale{p}.zip"),
                    log=log,
                )
            cf_zips.append(z)
        if da_cartella:
            cand = sorted(
                f
                for f in os.listdir(da_cartella)
                if f.startswith("uso_suolo_2023") and f.endswith(".zip")
            )
            if not cand:
                raise FileNotFoundError(
                    os.path.join(da_cartella, "uso_suolo_2023*.zip")
                )
            us_zip = os.path.join(da_cartella, cand[0])
        else:
            us_zip = _scarica(US_URL, os.path.join(tmp, "uso_suolo_2023.zip"), log=log)

        parti = _strati(cf_zips, us_zip, tmp, log=log)
        info_strati = _unisci_strati(parti, str(paths.SEMINATURALE_STRATI_PARQUET))
        per_cat = info_strati.pop("per_cat")
        n_strati = info_strati["poligoni"]
        log(
            "  strati: "
            + ", ".join(f"{c}/{f} {v:,.0f} ha" for (c, f), v in per_cat.items())
            + f" (memoria {_rss_gb():.1f} GB)"
        )

        info_mappa = _mappa(log=log)
        log("semi-naturale: residuo Small Woody Features, a riquadri")
        info_swf = _raster_swf(tmp, str(paths.SEMINATURALE_SWF_TIF), log=log)

    manifest = {
        "versioni": versioni,
        "strati": {
            "poligoni": int(n_strati),
            "mb": round(paths.SEMINATURALE_STRATI_PARQUET.stat().st_size / 1e6, 1),
            "ha": {f"{c}/{f}": float(v) for (c, f), v in per_cat.items()},
        },
        "mappa": info_mappa,
        "swf": info_swf,
        "secondi": round(time.time() - t0),
        "prodotto_il": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    paths.SEMINATURALE_MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False)
    )
    log(f"semi-naturale: fatto in {time.time() - t0:.0f}s")
    return {"aggiornato": True, **manifest}


def _impronta_regole() -> str:
    """Le tabelle delle classi fanno parte della versione: cambiarle deve rifare il ritaglio."""
    import hashlib

    regole = {
        "cf": config.SEMINATURAL_CF_STC,
        "us": config.SEMINATURAL_US_COD,
        "swf_escluse": list(config.SEMINATURAL_SWF_EXCLUDED_US),
        "margine": config.SEMINATURAL_SWF_ELEMENT_MARGIN_M,
    }
    return hashlib.sha1(json.dumps(regole, sort_keys=True).encode()).hexdigest()[:12]
