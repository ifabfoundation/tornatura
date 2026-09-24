"""Habitat di un organismo nel paesaggio dichiarato intorno a un campo.

Il primo organismo e' la cimice asiatica (Halyomorpha halys), ma il modulo e'
scritto per QUALSIASI organismo: ognuno e' una CARTELLA DI DATI in
`data/pests/<codice>/`, non codice:

  hosts.csv   specie AGREA (`cls`, la stessa colonna del parquet) -> livello ospite
              (principale | secondario | non_ospite | non_classificabile) e famiglia
              (permanente | erbacea | prato | seminaturale | altro)
  meta.json   nome, colture a cui si applica, cosa sono i suoi "serbatoi", etichette
              dei livelli, testi per l'interfaccia, fonti, versione della tabella

e il calcolo qui sotto e' unico. Aggiungere un organismo = aggiungere una cartella.

I livelli NON sono un giudizio di esperto: per la cimice discendono da una regola
dichiarata applicata a una matrice di evidenze con fonti (principale = danno
documentato in Italia o Europa da almeno due fonti indipendenti; secondario =
almeno un'evidenza di ospite; non_ospite = nessuna o negativa). La matrice, le
fonti e lo script sono in `esperimenti/cimice_landscape/ospiti/` e la versione
della tabella viaggia nella risposta (`hosts_version`).

Cosa si calcola, e perche' proprio questo (misurato il 24/09/2026 su 33 punti per
4 raggi, `esperimenti/cimice_landscape/`):
  - % di superficie per LIVELLO ospite, sul buffer e sul dichiarato, e separata per
    FAMIGLIA (frutteti vs erbacee): e' la metrica che la letteratura usa
    (Tamburini et al. 2023, composizione in buffer con miglior raggio 3000 m;
    Forresi et al. 2024, 200 m). La % a 500 m e a 3 km correlano solo 0,77 fra
    loro: sono due scale diverse, e per questo il servizio ammette 500 m.
  - i SERBATOI semi-naturali (bosco + siepi, boschetti, fasce, margini, fossi),
    riusando `agrea.seminatural`.
  - la DISTANZA bordo a bordo dal campo al frutteto ospite e alla siepe o bosco
    piu' vicini, pubblicata SOLO IN CLASSI: porta informazione parzialmente diversa
    dalla % (correlazione -0,80) e l'effetto bordo vive nei primi 50-100 m
    (Maistrello 2017, Bergh 2021).
Cosa NON si calcola, e perche': l'indice di connettivita' a kernel (correlato
0,85-0,97 con la % ospiti) e le metriche di configurazione FRAGSTATS (0,67-0,94)
sono risultati ridondanti; entrano solo se un dato di catture dimostrera' il
contrario, come chiesto dagli agronomi.

Anonimato, come nel resto del servizio: i totali per livello aggregano molte
specie; le prime specie ospiti seguono la regola dei tre appezzamenti
(`config.MIN_PARCELS_PER_ROW`); la distanza e' una classe e mai un numero di metri,
perche' una distanza precisa indicherebbe il campo di una singola azienda.

Il campo dell'utente va ESCLUSO dai patch quando si misurano le distanze (altrimenti
la distanza e' zero): con il `ring` del campo si escludono gli appezzamenti che lo
intersecano; senza, l'appezzamento dichiarato che contiene il centroide (stessa
logica di `agrea.parcel_at`); se non c'e', si misura dal punto.
"""

import csv
import json
import logging
import math
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import geopandas as gpd
import pandas as pd
from landscape import paths
from landscape.modules import agrea, config
from shapely.geometry import Point, Polygon

logger = logging.getLogger("landscape_pests")

PESTS_DIR = paths.DATA_DIR / "pests"
LEVELS = ("principale", "secondario", "non_ospite", "non_classificabile")
HOST_LEVELS = ("principale", "secondario")
FALLBACK_LEVEL = "non_classificabile"


class PestUnknown(KeyError):
    """Il codice organismo non corrisponde a nessuna cartella in data/pests."""


# --- registro degli organismi ---------------------------------------------------


@lru_cache(maxsize=None)
def registry() -> Dict[str, Dict[str, Any]]:
    """Tutti gli organismi presenti nel package, per codice."""
    out: Dict[str, Dict[str, Any]] = {}
    if not PESTS_DIR.exists():
        return out
    for meta_path in sorted(PESTS_DIR.glob("*/meta.json")):
        with meta_path.open(encoding="utf-8") as f:
            meta = json.load(f)
        code = meta.get("code") or meta_path.parent.name
        meta["code"] = code
        meta["_dir"] = str(meta_path.parent)
        out[code] = meta
    return out


def get_meta(code: str) -> Dict[str, Any]:
    meta = registry().get((code or "").strip())
    if meta is None:
        raise PestUnknown(code)
    return meta


def summary(meta: Dict[str, Any]) -> Dict[str, Any]:
    """La parte di `meta.json` che si espone sempre: identita' e versione."""
    return {
        "code": meta["code"],
        "label": meta.get("label"),
        "scientific_name": meta.get("scientific_name"),
        "eppo_code": meta.get("eppo_code"),
        "hosts_version": meta.get("hosts_version"),
        "applies_to_harvests": meta.get("applies_to_harvests"),
    }


def list_pests(harvest: Optional[str] = None) -> List[Dict[str, Any]]:
    """Gli organismi pertinenti a una coltura (tutti, se `applies_to_harvests` e' null)."""
    code = (harvest or "").strip()
    out = []
    for meta in registry().values():
        applies = meta.get("applies_to_harvests")
        if applies and code and code not in applies:
            continue
        out.append(summary(meta))
    return out


@lru_cache(maxsize=None)
def hosts(code: str) -> Dict[str, Tuple[str, str]]:
    """Tabella specie AGREA -> (livello, famiglia), letta una volta per organismo."""
    meta = get_meta(code)
    path = Path(meta["_dir"]) / meta.get("hosts_csv", "hosts.csv")
    table: Dict[str, Tuple[str, str]] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            livello = row.get("livello", "").strip() or FALLBACK_LEVEL
            if livello not in LEVELS:
                logger.warning(
                    "%s: livello sconosciuto '%s' per %s", code, livello, row.get("cls")
                )
                livello = FALLBACK_LEVEL
            table[row["cls"]] = (livello, row.get("famiglia", "").strip() or "altro")
    return table


def level_of(code: str, cls: Optional[str]) -> str:
    """Livello ospite di una specie dichiarata; una specie assente dalla tabella e'
    'non_classificabile' (habitat potenziale non attribuibile), mai un errore."""
    return hosts(code).get(str(cls), (FALLBACK_LEVEL, "altro"))[0]


def annotate_features(features: List[Dict[str, Any]], code: str) -> None:
    """Aggiunge `host_level` alle feature di /parcels: e' il server a fare il join,
    il client si limita a filtrare e colorare."""
    table = hosts(code)
    for f in features:
        props = f.setdefault("properties", {})
        props["host_level"] = table.get(
            str(props.get("declared")), (FALLBACK_LEVEL, None)
        )[0]


# --- geometria del campo ---------------------------------------------------------


def parse_ring(ring: Optional[str]) -> Optional[Polygon]:
    """`lng,lat;lng,lat;...` -> poligono in EPSG:4326, o None se non usabile.

    Il formato compatto sta in una query string: un anello di campo ha di norma
    10-50 vertici. Il tetto sui vertici protegge il servizio da input abnormi.
    """
    if not ring:
        return None
    punti: List[Tuple[float, float]] = []
    for pezzo in ring.split(";"):
        pezzo = pezzo.strip()
        if not pezzo:
            continue
        lng_s, lat_s = pezzo.split(",")
        punti.append((float(lng_s), float(lat_s)))
    if len(punti) > config.PEST_RING_MAX_VERTICES:
        raise ValueError("ring has too many vertices")
    if len(punti) < 3:
        return None
    if punti[0] != punti[-1]:
        punti.append(punti[0])
    poly = Polygon(punti)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly if (poly is not None and not poly.is_empty) else None


def distance_class(d: Optional[float]) -> Dict[str, Any]:
    """Classe di distanza, mai il numero: `< 100 m` e' 'confinante o quasi'."""
    if d is None or (isinstance(d, float) and math.isnan(d)):
        return {"class": "none_in_radius", "label": "nessuno entro il raggio"}
    limiti = list(config.PEST_NEAREST_CLASSES_M)
    if d < limiti[0]:
        return {"class": f"lt_{limiti[0]}", "label": f"entro {limiti[0]} m"}
    for a, b in zip(limiti, limiti[1:]):
        if d < b:
            return {"class": f"{a}_{b}", "label": f"{a}-{b} m"}
    return {"class": f"gt_{limiti[-1]}", "label": f"oltre {limiti[-1]} m"}


def _min_or_nan(s: pd.Series) -> float:
    return float(s.min()) if len(s) else float("nan")


# --- il calcolo ------------------------------------------------------------------


def habitat(
    lat: float,
    lng: float,
    radius_m: float,
    harvest: Optional[str] = None,
    ring: Optional[str] = None,
    pest: str = config.PEST_DEFAULT,
) -> Dict[str, Any]:
    """Quanto il paesaggio dichiarato intorno al punto ospita l'organismo.

    Restituisce sempre un dizionario; `available: False` con `reason` quando i
    dati non ci sono, che NON e' un errore: la pagina non mostra la sezione.
    """
    meta = get_meta(pest)
    table = hosts(pest)
    base: Dict[str, Any] = {
        "pest": summary(meta),
        "location": {"lat": lat, "lng": lng},
        "radius_m": int(radius_m),
        "source": config.AGREA_SOURCE,
        "year": config.AGREA_YEAR,
    }
    if not agrea.available():
        return {
            **base,
            "available": False,
            "reason": "dati dichiarativi non disponibili",
        }

    metrico, _, bbox = agrea._buffer(lat, lng, radius_m)
    buffer_ha = metrico.area / 10_000
    g = agrea.parcels(lat, lng, radius_m, harvest)
    if g.empty:
        return {
            **base,
            "available": False,
            "reason": "nessun appezzamento dichiarato nel raggio",
        }

    g = g.assign(
        livello=g["cls"].map(lambda c: table.get(str(c), (FALLBACK_LEVEL, None))[0]),
        famiglia=g["cls"].map(
            lambda c: (table.get(str(c)) or (None, None))[1] or "altro"
        ),
    )
    declared_ha = float(g["ha_in_buffer"].sum())
    agri = g[g["is_crop_class"]] if "is_crop_class" in g.columns else g
    agri_ha = float(agri["ha_in_buffer"].sum())

    def quota(sub: pd.DataFrame) -> Dict[str, Any]:
        ha = float(sub["ha_in_buffer"].sum()) if not sub.empty else 0.0
        return {
            "ha": round(ha, 1),
            "pct_of_buffer": round(100 * ha / buffer_ha, 1) if buffer_ha else 0.0,
            "pct_of_declared": round(100 * ha / declared_ha, 1) if declared_ha else 0.0,
            "parcels": int(len(sub)),
        }

    etichette = meta.get("levels", {})
    levels = {
        liv: {
            **quota(g[g["livello"] == liv]),
            "label": etichette.get(liv, {}).get("label", liv),
        }
        for liv in LEVELS
    }
    host = g[g["livello"].isin(HOST_LEVELS)]
    hosts_block = {
        **quota(host),
        "by_family": {
            fam: quota(host[host["famiglia"] == fam])
            for fam in ("permanente", "erbacea")
        },
    }

    # Le prime specie ospiti, con la regola dei tre appezzamenti.
    top: List[Dict[str, Any]] = []
    if not host.empty:
        grouped = (
            host.groupby("cls")
            .agg(
                ha=("ha_in_buffer", "sum"),
                parcels=("ha_in_buffer", "size"),
                livello=("livello", "first"),
                famiglia=("famiglia", "first"),
            )
            .sort_values("ha", ascending=False)
        )
        grouped = grouped[grouped["parcels"] >= config.MIN_PARCELS_PER_ROW].head(6)
        for cls, row in grouped.iterrows():
            top.append(
                {
                    "species": agrea.display_name(str(cls)),
                    "declared": str(cls),
                    "level": str(row["livello"]),
                    "family": str(row["famiglia"]),
                    "ha": round(float(row["ha"]), 1),
                    "pct_of_declared": round(100 * float(row["ha"]) / declared_ha, 1)
                    if declared_ha
                    else 0.0,
                    "parcels": int(row["parcels"]),
                }
            )

    # Serbatoi semi-naturali: la stessa misura della pagina, con l'etichetta dell'organismo.
    reservoirs = agrea.seminatural(lat, lng, radius_m)
    reservoirs["label"] = meta.get("reservoirs", {}).get(
        "label", "Serbatoi semi-naturali"
    )

    # --- distanze bordo a bordo, dal campo, escludendo il campo stesso ---------
    metric = g.geometry.to_crs(config.METRIC_EPSG)
    field_poly = parse_ring(ring)
    field_declared: Optional[Dict[str, Any]] = None
    if field_poly is not None:
        field_m = (
            gpd.GeoSeries([field_poly], crs=4326).to_crs(config.METRIC_EPSG).iloc[0]
        )
        exclude = metric.intersects(field_m)
        origin = "ring"
    else:
        punto_m = (
            gpd.GeoSeries([Point(lng, lat)], crs=4326)
            .to_crs(config.METRIC_EPSG)
            .iloc[0]
        )
        contiene = metric.contains(punto_m)
        if bool(contiene.any()):
            idx = metric[contiene].area.idxmin()
            field_m = metric.loc[idx]
            exclude = pd.Series(False, index=g.index)
            exclude.loc[idx] = True
            origin = "declared_parcel"
            field_declared = {
                "species": agrea.display_name(str(g.loc[idx, "cls"])),
                "level": str(g.loc[idx, "livello"]),
            }
        else:
            field_m = punto_m
            exclude = pd.Series(False, index=g.index)
            origin = "centroid"

    patches = g[~exclude.values]
    d = metric[~exclude.values].distance(field_m)
    res_cfg = meta.get("reservoirs", {})
    reservoir_classes = {str(c).upper() for c in res_cfg.get("classes", ["BOSCO"])}
    nearest_cfg = meta.get(
        "nearest",
        {"host_orchard": {"levels": ["principale"], "families": ["permanente"]}},
    )
    nearest: Dict[str, Any] = {}
    for key, spec in nearest_cfg.items():
        mask = patches["livello"].isin(spec.get("levels", HOST_LEVELS))
        if spec.get("families"):
            mask &= patches["famiglia"].isin(spec["families"])
        nearest[key] = {
            **distance_class(_min_or_nan(d[mask.values])),
            "label_target": spec.get("label", key),
        }

    d_semi = [d[patches["cls"].astype(str).str.upper().isin(reservoir_classes).values]]
    if res_cfg.get("elements", True) and agrea.elements_available():
        e = agrea._leggi(paths.AGREA_ELEMENTI_PARQUET, bbox)
        if not e.empty:
            d_semi.append(e.geometry.to_crs(config.METRIC_EPSG).distance(field_m))
    nearest["seminatural"] = {
        **distance_class(_min_or_nan(pd.concat(d_semi)) if d_semi else float("nan")),
        "label_target": res_cfg.get("nearest_label", "siepe, boschetto o bosco"),
    }

    return {
        **base,
        "available": True,
        "buffer_ha": round(buffer_ha, 1),
        "declared_ha": round(declared_ha, 1),
        "declared_pct_of_buffer": round(100 * declared_ha / buffer_ha, 1)
        if buffer_ha
        else 0.0,
        "agri_ha": round(agri_ha, 1),
        "levels": levels,
        "hosts": hosts_block,
        "top_hosts": top,
        "min_parcels_per_row": config.MIN_PARCELS_PER_ROW,
        "reservoirs": reservoirs,
        "nearest": nearest,
        "nearest_origin": origin,
        "field": field_declared,
        "texts": meta.get("texts", {}),
        "limits": meta.get("limits", []),
        "sources": meta.get("sources", []),
    }
