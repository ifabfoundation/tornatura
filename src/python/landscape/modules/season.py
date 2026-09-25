"""Finestra stagionale: quali ospiti intorno al campo sono OGGI nella fase che l'organismo attacca.

Completa `pests.habitat`, che dice quanti ospiti ci sono: qui si dice in che fase sono. Per ogni
appezzamento ospite nel cerchio:

  1. la coltura dei bollettini corrispondente alla specie AGREA
     (`data/phenology/agrea_bollettini.json`, generico per tutti gli organismi);
  2. la sua fase nella zona del punto, dal servizio **bollettini** (`/v1/bollettini/fenologia`:
     testo del bollettino di produzione integrata e intervallo BBCH). Se il servizio non
     risponde, dal **calendario di riserva** del 2026 (`data/phenology/calendario_er_2026.csv`,
     stessa tabella verificata), alla stessa data dell'anno; la risposta dice sempre da dove
     arriva il dato (`source`);
  3. la classe rispetto alla finestra dell'organismo (`meta.json`, chiave `season.windows`, con le
     fonti): attivo se l'intervallo BBCH tocca la finestra attiva, in arrivo se tocca solo lo
     stadio prima, concluso se sta tutto oltre, non ancora altrimenti.

Regole dichiarate (le stesse dell'esperimento `esperimenti/cimice_landscape/fenologia/curva.py`):
  - una fase vale per 14 giorni (bollettini settimanali); oltre, "fase non disponibile";
  - "concluso" e' uno stato finale: se una coltura e' uscita dal bollettino dopo una fase
    conclusa (raccolta), resta conclusa. Nessuna serie del 2026 torna indietro (controllato);
  - "attivo" quando l'intervallo supera la finestra solo in parte (es. "da fioritura ad
    allegagione") si conta anche in `partial_active_ha`;
  - direzione: ogni pezzo di appezzamento va nel settore di 45 gradi (N, NE, ...) del suo
    baricentro visto dal punto. Un settore mostra gli ettari solo se ha almeno
    `MIN_PARCELS_PER_ROW` appezzamenti, come le righe per specie della pagina. Le "direzioni
    principali" sono i settori con almeno un quarto degli ettari attivi (al piu' tre): con otto
    settori una distribuzione uniforme ne darebbe un ottavo ciascuno, quindi nessuno.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import logging
import math
import time
import urllib.parse
import urllib.request
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import geopandas as gpd
from landscape import paths
from landscape.modules import agrea, config, pests
from shapely.geometry import Point

logger = logging.getLogger("landscape_season")

PHENOLOGY_DIR = paths.DATA_DIR / "phenology"
SECTORS = ("N", "NE", "E", "SE", "S", "SO", "O", "NO")
SECTOR_LABEL = {
    "N": "nord",
    "NE": "nord-est",
    "E": "est",
    "SE": "sud-est",
    "S": "sud",
    "SO": "sud-ovest",
    "O": "ovest",
    "NO": "nord-ovest",
}
AREA_TOLERANCE_M = 2000
CLASSES = ("active", "arriving", "not_yet", "over", "no_phase", "no_window")

_cache: Dict[Tuple[float, float, str], Tuple[float, Optional[Dict[str, Any]]]] = {}


# --- dati statici -----------------------------------------------------------------


@lru_cache(maxsize=None)
def crop_map() -> Dict[str, Any]:
    with (PHENOLOGY_DIR / "agrea_bollettini.json").open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=None)
def areas() -> gpd.GeoDataFrame:
    return gpd.read_file(PHENOLOGY_DIR / "aree_bollettini_er.geojson")


def area_of(lat: float, lng: float) -> Optional[str]:
    """Zona dei bollettini che contiene il punto; se il punto cade in una fessura fra due zone
    (i confini sono semplificati), la zona piu' vicina entro `AREA_TOLERANCE_M`."""
    a = areas()
    pt = Point(lng, lat)
    hit = a[a.geometry.contains(pt)]
    if not hit.empty:
        return str(hit.iloc[0]["area"])
    am = a.to_crs(config.METRIC_EPSG)
    ptm = gpd.GeoSeries([pt], crs=4326).to_crs(config.METRIC_EPSG).iloc[0]
    d = am.geometry.distance(ptm)
    if len(d) and float(d.min()) <= AREA_TOLERANCE_M:
        return str(am.loc[d.idxmin(), "area"])
    return None


@lru_cache(maxsize=None)
def calendar() -> Dict[str, Dict[str, List[Tuple[dt.date, int, int, str]]]]:
    """{area: {coltura: [(data, bbch_min, bbch_max, diciture)]}} ordinato per data."""
    out: Dict[str, Dict[str, List[Tuple[dt.date, int, int, str]]]] = {}
    with (PHENOLOGY_DIR / "calendario_er_2026.csv").open(
        encoding="utf-8", newline=""
    ) as f:
        for r in csv.DictReader(f):
            out.setdefault(r["area"], {}).setdefault(r["coltura"], []).append(
                (
                    dt.date.fromisoformat(r["data"]),
                    int(r["bbch_min"]),
                    int(r["bbch_max"]),
                    r["fasi"],
                )
            )
    for per in out.values():
        for serie in per.values():
            serie.sort()
    return out


# --- fasi: servizio bollettini o calendario ----------------------------------------


def _from_bulletins(
    lat: float, lng: float, on: dt.date
) -> Tuple[Optional[Dict[str, Any]], str]:
    """(risposta di /v1/bollettini/fenologia, motivo). Risposta None se non usabile; il motivo
    dice perche' (servizio non configurato, non raggiungibile, o senza dati per il punto).
    Si mettono in cache solo le risposte arrivate: un errore si riprova alla richiesta dopo.
    """
    base = config.BOLLETTINI_API_URL
    if not base:
        return None, "bulletins_not_configured"
    chiave = (round(lat, 3), round(lng, 3), on.isoformat())
    ora = time.monotonic()
    hit = _cache.get(chiave)
    if hit and ora - hit[0] < config.PHENOLOGY_CACHE_S:
        return hit[1], "cache"
    url = f"{base.rstrip('/')}/v1/bollettini/fenologia?" + urllib.parse.urlencode(
        {"lat": lat, "lng": lng, "date": on.isoformat()}
    )
    try:
        with urllib.request.urlopen(url, timeout=config.PHENOLOGY_TIMEOUT_S) as r:
            data = json.load(r)
    except Exception as e:  # servizio giu', rete, 404: si passa al calendario
        logger.warning("fenologia dai bollettini non disponibile (%s): %s", url, e)
        return None, "bulletins_unreachable"
    if len(_cache) > 2048:
        _cache.clear()
    if not data.get("available"):
        _cache[chiave] = (ora, None)
        return None, "bulletins_no_data"
    _cache[chiave] = (ora, data)
    return data, "ok"


def _from_calendar(area: str, on: dt.date) -> Dict[str, Any]:
    """Il calendario 2026 alla stessa data dell'anno (stesse regole dell'archivio bollettini)."""
    try:
        giorno = on.replace(year=2026)
    except ValueError:  # 29 febbraio
        giorno = on.replace(year=2026, day=28)
    crops: Dict[str, Any] = {}
    for coltura, serie in calendar().get(area, {}).items():
        prima = [x for x in serie if x[0] <= giorno]
        if not prima:
            continue
        d, lo, hi, fasi = prima[-1]
        eta = (giorno - d).days
        crops[coltura] = {
            "bulletin_date": d.isoformat(),
            "age_days": eta,
            "stale": eta > config.PHENOLOGY_VALIDITY_DAYS,
            "phases": fasi.split(" || "),
            "bbch_min": lo,
            "bbch_max": hi,
        }
    return {"area": area, "crops": crops}


def phases(lat: float, lng: float, on: dt.date) -> Dict[str, Any]:
    """Fasi per coltura nella zona del punto, con la provenienza dichiarata."""
    b, motivo = _from_bulletins(lat, lng, on)
    if b is None and motivo == "cache":
        motivo = "bulletins_no_data"
    if b is not None:
        return {
            "source": "bulletins",
            "fallback_reason": None,
            "area": b.get("area"),
            "crops": b.get("crops", {}),
            "last_bulletin": b.get("last_bulletin"),
        }
    area = area_of(lat, lng)
    if area is None:
        return {"source": "none", "fallback_reason": motivo, "area": None, "crops": {}}
    c = _from_calendar(area, on)
    return {
        "source": "calendar_2026",
        "fallback_reason": motivo,
        "area": area,
        "crops": c["crops"],
        "last_bulletin": None,
    }


# --- classi -------------------------------------------------------------------------


def classify(window: Dict[str, Any], lo: int, hi: int) -> str:
    a0, a1 = window["active"]
    r0, r1 = window["arriving"]
    if hi >= a0 and lo <= a1:
        return "active"
    if lo > a1:
        return "over"
    if hi >= r0 and lo <= r1:
        return "arriving"
    return "not_yet"


def _crop_state(
    cls: str, crops: Dict[str, Any], windows: Dict[str, Any]
) -> Dict[str, Any]:
    """Classe di una specie AGREA: dalla coltura del bollettino corrispondente."""
    m = crop_map()
    colture = m["specie"].get(cls)
    if not colture or not any(c in windows for c in colture):
        return {"class": "no_window"}
    if cls in m.get("prima_disponibile", []):
        # la prima sezione del bollettino che ha davvero un intervallo BBCH
        colture = [
            c for c in colture if c in crops and crops[c].get("bbch_min") is not None
        ][:1] or colture[:1]
    valide = [
        (c, crops[c])
        for c in colture
        if c in crops and crops[c].get("bbch_min") is not None
    ]
    fresche = [(c, x) for c, x in valide if not x.get("stale")]
    finestra = windows[next(c for c in colture if c in windows)]
    if not fresche:
        # "concluso" e' finale: una coltura tolta dal bollettino dopo la raccolta resta conclusa
        # (per l'unione, es. il susino, conta solo la voce piu' recente: le sezioni europeo e
        # cino-giapponese si fermano ad aprile, la sezione unica prosegue fino alla raccolta)
        ultima = max((x["bulletin_date"] for _, x in valide), default=None)
        vecchie = [
            classify(finestra, x["bbch_min"], x["bbch_max"])
            for c, x in valide
            if x["bulletin_date"] == ultima
        ]
        if vecchie and all(v == "over" for v in vecchie):
            return {"class": "over", "crops": [c for c, _ in valide], "stale": True}
        return {"class": "no_phase", "crops": colture}
    lo = min(x["bbch_min"] for _, x in fresche)
    hi = max(x["bbch_max"] for _, x in fresche)
    classe = classify(finestra, lo, hi)
    parziale = classe == "active" and (
        lo < finestra["active"][0] or hi > finestra["active"][1]
    )
    return {
        "class": classe,
        "partial": parziale,
        "bbch_min": lo,
        "bbch_max": hi,
        "crops": [c for c, _ in fresche],
        "phases": [p for _, x in fresche for p in x.get("phases", [])],
        "bulletin_date": max(x["bulletin_date"] for _, x in fresche),
    }


def _sector(dx: float, dy: float) -> str:
    ang = (math.degrees(math.atan2(dx, dy)) + 360) % 360
    return SECTORS[int(((ang + 22.5) % 360) // 45)]


# --- il calcolo -----------------------------------------------------------------------


def season(
    lat: float,
    lng: float,
    radius_m: float,
    on: Optional[dt.date] = None,
    pest: str = config.PEST_DEFAULT,
) -> Dict[str, Any]:
    meta = pests.get_meta(pest)
    on = on or dt.date.today()
    base: Dict[str, Any] = {
        "pest": pests.summary(meta),
        "date": on.isoformat(),
        "radius_m": int(radius_m),
        "location": {"lat": lat, "lng": lng},
    }
    windows = (meta.get("season") or {}).get("windows")
    if not windows:
        return {
            **base,
            "available": False,
            "reason": "nessuna finestra stagionale per questo organismo",
        }
    if not agrea.available():
        return {
            **base,
            "available": False,
            "reason": "dati dichiarativi non disponibili",
        }
    g = agrea.parcels(lat, lng, radius_m, None)
    table = pests.hosts(pest)
    if g.empty:
        return {
            **base,
            "available": False,
            "reason": "nessun appezzamento dichiarato nel raggio",
        }
    g = g[
        g["cls"]
        .map(lambda c: table.get(str(c), (pests.FALLBACK_LEVEL, None))[0])
        .isin(pests.HOST_LEVELS)
    ]
    if g.empty:
        return {**base, "available": False, "reason": "nessun ospite nel raggio"}

    ph = phases(lat, lng, on)
    if ph["source"] == "none":
        return {
            **base,
            "available": False,
            "reason": "punto fuori dalle zone dei bollettini dell'Emilia-Romagna",
        }
    stati = {
        cls: _crop_state(str(cls), ph["crops"], windows) for cls in g["cls"].unique()
    }

    # direzione: baricentro di ogni pezzo visto dal punto, in metri
    metric = g.geometry.to_crs(config.METRIC_EPSG)
    centro = (
        gpd.GeoSeries([Point(lng, lat)], crs=4326).to_crs(config.METRIC_EPSG).iloc[0]
    )
    cent = metric.centroid
    # l'appezzamento che contiene il punto e' il campo stesso (o il suo vicino di bordo): non
    # indica una direzione, va al "centro"
    sotto = metric.contains(centro).values
    g = g.assign(
        classe=g["cls"].map(lambda c: stati[c]["class"]),
        parziale=g["cls"].map(lambda c: bool(stati[c].get("partial"))),
        settore=[
            "centro" if dentro else _sector(p.x - centro.x, p.y - centro.y)
            for p, dentro in zip(cent, sotto)
        ],
    )
    host_ha = float(g["ha_in_buffer"].sum())

    def blocco(sub) -> Dict[str, Any]:
        ha = float(sub["ha_in_buffer"].sum())
        return {
            "ha": round(ha, 1),
            "pct_of_hosts": round(100 * ha / host_ha, 1) if host_ha else 0.0,
            "parcels": int(len(sub)),
        }

    classes = {c: blocco(g[g["classe"] == c]) for c in CLASSES}
    labels = (meta.get("season") or {}).get("classes", {})
    for c in CLASSES:
        classes[c]["label"] = labels.get(c, c)

    # per coltura: solo le righe con almeno MIN_PARCELS_PER_ROW appezzamenti, come nella pagina
    righe: List[Dict[str, Any]] = []
    for cls, sub in g.groupby("cls"):
        st = stati[cls]
        if len(sub) < config.MIN_PARCELS_PER_ROW:
            continue
        righe.append(
            {
                "species": agrea.display_name(str(cls)),
                "declared": str(cls),
                "class": st["class"],
                "partial": bool(st.get("partial")),
                "ha": round(float(sub["ha_in_buffer"].sum()), 1),
                "parcels": int(len(sub)),
                "phases": st.get("phases", []),
                "bbch_min": st.get("bbch_min"),
                "bbch_max": st.get("bbch_max"),
                "bulletin_date": st.get("bulletin_date"),
            }
        )
    ordine = {c: i for i, c in enumerate(CLASSES)}
    righe.sort(key=lambda r: (ordine[r["class"]], -r["ha"]))

    sectors = []
    for s in SECTORS:
        sub = g[g["settore"] == s]
        att = sub[sub["classe"] == "active"]
        arr = sub[sub["classe"] == "arriving"]
        ok = len(sub) >= config.MIN_PARCELS_PER_ROW
        sectors.append(
            {
                "sector": s,
                "label": SECTOR_LABEL[s],
                "parcels": int(len(sub)),
                "shown": ok,
                "active_ha": round(float(att["ha_in_buffer"].sum()), 1) if ok else None,
                "arriving_ha": round(float(arr["ha_in_buffer"].sum()), 1)
                if ok
                else None,
            }
        )
    att_tot = float(
        g[(g["classe"] == "active") & (g["settore"] != "centro")]["ha_in_buffer"].sum()
    )
    principali = [
        x
        for x in sectors
        if x["shown"] and att_tot and (x["active_ha"] or 0) >= 0.25 * att_tot
    ]
    principali.sort(key=lambda x: -(x["active_ha"] or 0))

    return {
        **base,
        "available": True,
        "source": ph["source"],
        "area": ph["area"],
        "last_bulletin": ph.get("last_bulletin"),
        "fallback_reason": ph.get("fallback_reason"),
        "active_ha_directional": round(att_tot, 1),
        "validity_days": config.PHENOLOGY_VALIDITY_DAYS,
        "hosts_ha": round(host_ha, 1),
        "classes": classes,
        "partial_active_ha": round(float(g[g["parziale"]]["ha_in_buffer"].sum()), 1),
        "crops": righe,
        "sectors": sectors,
        "main_directions": [x["sector"] for x in principali[:3]],
        "min_parcels_per_row": config.MIN_PARCELS_PER_ROW,
        "windows": windows,
        "method": (
            "Fase di ogni coltura ospite dal bollettino di produzione integrata della zona (ultimo "
            "bollettino, validita' 14 giorni), tradotta in codici BBCH con un dizionario verificato e "
            "confrontata con la finestra di suscettibilita' dell'organismo, con le sue fonti."
        ),
    }
