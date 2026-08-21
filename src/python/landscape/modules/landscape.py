"""Analisi della composizione colturale intorno a un punto.

Logica portata dall'app di prototipazione `crop_class_map` (Streamlit), qui
isolata in funzioni pure: nessuna dipendenza dall'interfaccia, nessuno stato
globale oltre alla cache del dataset.

Il calcolo delle superfici e' invariato rispetto al prototipo, dove era stato
validato contro la colonna ufficiale `Area_HA` di ARPAE:
  - il buffer e la geometria delle particelle sono proiettati in UTM 32N;
  - le particelle sono RITAGLIATE sul buffer, cosi' un appezzamento a cavallo
    del bordo contribuisce solo per la parte interna;
  - le percentuali sono calcolate sulle superfici (ettari), non sui conteggi.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

import geopandas as gpd
import shapely
from landscape import paths
from landscape.modules import agrea, config
from shapely.geometry import Point

# Cache del dataset: caricato una volta sola, riusato da tutte le richieste.
_GDF: Optional[gpd.GeoDataFrame] = None


class DatasetUnavailable(RuntimeError):
    """Il file del dataset non e' presente o non e' leggibile."""


def load_dataset() -> gpd.GeoDataFrame:
    """Carica il dataset iColt (memoizzato)."""
    global _GDF
    if _GDF is not None:
        return _GDF

    if not paths.ICOLT_PARQUET.exists():
        raise DatasetUnavailable(f"dataset not found at {paths.ICOLT_PARQUET}")

    try:
        gdf = gpd.read_parquet(paths.ICOLT_PARQUET)
    except Exception as exc:  # pragma: no cover - dipende dall'ambiente
        raise DatasetUnavailable(str(exc)) from exc

    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    gdf["crop_class"] = gdf["ID_CROP"].map(
        lambda code: config.CROP_CLASS_MAP.get(code, config.UNKNOWN_CLASS)
    )
    gdf["is_agri"] = ~gdf["ID_CROP"].isin(config.NON_AGRI_CODES)

    _GDF = gdf
    return _GDF


def dataset_bounds() -> Tuple[float, float, float, float]:
    """Bounding box del dataset in EPSG:4326 (minx, miny, maxx, maxy)."""
    minx, miny, maxx, maxy = load_dataset().total_bounds
    return float(minx), float(miny), float(maxx), float(maxy)


def is_covered(lat: float, lng: float) -> bool:
    """Vero se il punto ricade nell'area coperta dal dataset."""
    minx, miny, maxx, maxy = dataset_bounds()
    return (minx <= lng <= maxx) and (miny <= lat <= maxy)


def coverage() -> Dict[str, Any]:
    """Descrive copertura e contenuto del dataset (usata dal frontend)."""
    gdf = load_dataset()
    minx, miny, maxx, maxy = dataset_bounds()
    classes = sorted(gdf.loc[gdf["is_agri"], "crop_class"].unique().tolist())
    return {
        "dataset": {
            "source": config.DATASET_SOURCE,
            "year": config.DATASET_YEAR,
            "region": config.COVERAGE_REGION,
            "min_parcel_ha": config.MIN_PARCEL_HA,
        },
        "bbox": {"min_lng": minx, "min_lat": miny, "max_lng": maxx, "max_lat": maxy},
        "parcels": int(len(gdf)),
        "agri_classes": classes,
        "mappable_harvests": sorted(config.HARVEST_TO_ICOLT.keys()),
        "radius_m": {
            "default": config.DEFAULT_RADIUS_M,
            "min": config.MIN_RADIUS_M,
            "max": config.MAX_RADIUS_M,
        },
    }


def resolve_crop(harvest: Optional[str]) -> Optional[Dict[str, Any]]:
    """Traduce un codice coltura di tornatura nella classe iColt corrispondente.

    Restituisce sempre un esito esplicito: quando la coltura non e'
    distinguibile nel dataset, `mappable` e' False e `reason` dice perche'.
    Se non e' stata chiesta nessuna coltura restituisce None: non e' un caso
    non mappabile, e' l'assenza della domanda.
    """
    if not harvest:
        return None

    code = harvest.strip()
    if code in config.HARVEST_TO_ICOLT:
        return {
            "harvest": code,
            "icolt_class": config.HARVEST_TO_ICOLT[code],
            "mappable": True,
            "reason": None,
        }
    if code in config.HARVEST_AGGREGATED:
        return {
            "harvest": code,
            "icolt_class": config.HARVEST_AGGREGATED[code],
            "mappable": False,
            "reason": config.REASON_AGGREGATED,
        }
    if code in config.HARVEST_NOT_IN_DATASET:
        return {
            "harvest": code,
            "icolt_class": None,
            "mappable": False,
            "reason": config.REASON_NOT_IN_DATASET,
        }
    return {
        "harvest": code,
        "icolt_class": None,
        "mappable": False,
        "reason": config.REASON_UNKNOWN,
    }


def observability(lat: float, lng: float) -> Dict[str, Any]:
    """Quanta parte dell'intorno il dato riesce a vedere, a raggio FISSO.

    Deciso su config.OBSERVABILITY_RADIUS_M e NON sul raggio scelto dall'utente:
    altrimenti il selettore annulla il controllo. Misurato a Brisighella: 0,0%
    cartografato a 3 km ma 9,4% a 10 km, e quel 9,4% descrive la pianura di
    Faenza, non il paesaggio dell'utente.

    Restituisce lo stato ("full" / "partial" / "suppressed"), la frazione
    cartografata e la sua distribuzione per quadrante: se la copertura e'
    concentrata da un lato — il caso pedecollinare — la percentuale complessiva
    non lo comunica.
    """
    r = config.OBSERVABILITY_RADIUS_M
    parcels, buffer_ha = analyze(lat, lng, r, keep_clipped=True)
    mapped_ha = float(parcels["ha_in_buffer"].sum()) if not parcels.empty else 0.0
    pct = round(100 * mapped_ha / buffer_ha, 1) if buffer_ha else 0.0

    # quota cartografata per quadrante (NE, NW, SW, SE) rispetto al centro
    quadranti = [0.0, 0.0, 0.0, 0.0]
    if not parcels.empty:
        metric = parcels.to_crs(config.METRIC_EPSG)
        cx, cy = (
            gpd.GeoSeries([Point(lng, lat)], crs=4326)
            .to_crs(config.METRIC_EPSG)
            .iloc[0]
            .coords[0]
        )
        for geom in metric.geometry:
            c = geom.centroid
            i = (0 if c.y >= cy else 2) + (0 if c.x >= cx else 1)
            quadranti[i] += geom.area / 10_000
        quarto = buffer_ha / 4 if buffer_ha else 1.0
        quadranti = [round(100 * q / quarto, 1) for q in quadranti]

    peggior_quadrante = min(quadranti) if quadranti else 0.0
    if pct < config.OBSERVABILITY_SUPPRESS_PCT:
        stato = "suppressed"
    elif (
        pct < config.OBSERVABILITY_PARTIAL_PCT
        or peggior_quadrante < config.OBSERVABILITY_MIN_QUADRANT_PCT
    ):
        stato = "partial"
    else:
        stato = "full"

    return {
        "status": stato,
        "radius_m": r,
        "mapped_pct": pct,
        "quadrant_pct": quadranti,
        "worst_quadrant_pct": peggior_quadrante,
    }


def coverage_note(harvest: Optional[str]) -> Optional[str]:
    """Nota di sottostima per le colture che iColt vede male (vite, olivo)."""
    if not harvest:
        return None
    return config.HARVEST_COVERAGE_NOTE.get(harvest.strip())


def buffer_polygon(lat: float, lng: float, radius_m: float):
    """Buffer circolare in EPSG:4326, identico a quello usato da analyze().

    Serve al frontend per disegnare esattamente l'area su cui i numeri sono
    calcolati, invece di ricostruirla con un'approssimazione diversa.
    """
    center_metric = gpd.GeoSeries([Point(lng, lat)], crs=4326).to_crs(
        config.METRIC_EPSG
    )
    buffer_metric = center_metric.buffer(radius_m).iloc[0]
    return gpd.GeoSeries([buffer_metric], crs=config.METRIC_EPSG).to_crs(4326).iloc[0]


def analyze(lat: float, lng: float, radius_m: float, keep_clipped: bool = False):
    """Ritaglia il dataset sul buffer intorno al punto.

    Restituisce (particelle_con_ettari, buffer_ha). Con keep_clipped=True la
    geometria restituita e' quella RITAGLIATA sul buffer: cosi' quello che la
    mappa disegna coincide con gli ettari che il servizio dichiara.
    """
    gdf = load_dataset()

    center_metric = gpd.GeoSeries([Point(lng, lat)], crs=4326).to_crs(
        config.METRIC_EPSG
    )
    buffer_metric = center_metric.buffer(radius_m).iloc[0]
    buffer_geo = (
        gpd.GeoSeries([buffer_metric], crs=config.METRIC_EPSG).to_crs(4326).iloc[0]
    )
    buffer_ha = buffer_metric.area / 10_000

    idx = gdf.sindex.query(buffer_geo, predicate="intersects")
    parcels = gdf.iloc[idx].copy()
    if parcels.empty:
        parcels["ha_in_buffer"] = []
        return parcels, buffer_ha

    metric_geoms = parcels.geometry.to_crs(config.METRIC_EPSG).make_valid()
    clipped = metric_geoms.intersection(buffer_metric)
    parcels["ha_in_buffer"] = clipped.area / 10_000
    if keep_clipped:
        parcels = parcels.set_geometry(
            gpd.GeoSeries(
                clipped.values, index=parcels.index, crs=config.METRIC_EPSG
            ).to_crs(4326)
        )
    parcels = parcels[parcels["ha_in_buffer"] > 0.001]
    return parcels, buffer_ha


def composition(
    lat: float, lng: float, radius_m: float, harvest: Optional[str] = None
) -> Dict[str, Any]:
    """Composizione colturale del paesaggio intorno al punto."""
    parcels, buffer_ha = analyze(lat, lng, radius_m)
    agri = parcels[parcels["is_agri"]]

    agri_ha = float(agri["ha_in_buffer"].sum()) if not agri.empty else 0.0
    crop = resolve_crop(harvest)

    breakdown: List[Dict[str, Any]] = []
    if not agri.empty:
        grouped = (
            agri.groupby("crop_class")
            .agg(ha=("ha_in_buffer", "sum"), parcels=("ha_in_buffer", "size"))
            .sort_values("ha", ascending=False)
        )
        # Le classi sostenute da pochi appezzamenti sono singole aziende, non
        # paesaggio: si accorpano e il conteggio non si pubblica.
        residuo_ha = 0.0
        residuo_classi = 0
        for crop_class, row in grouped.iterrows():
            n = int(row["parcels"])
            ha = float(row["ha"])
            if n < config.MIN_PARCELS_PER_ROW:
                residuo_ha += ha
                residuo_classi += 1
                continue
            breakdown.append(
                {
                    "icolt_class": str(crop_class),
                    "family": config.CLASS_FAMILY.get(
                        str(crop_class), config.FAMILY_OTHER
                    ),
                    "ha": round(ha, 1),
                    "pct": round(100 * ha / agri_ha, 1) if agri_ha else 0.0,
                    "parcels": n,
                }
            )
        if residuo_ha > 0:
            breakdown.append(
                {
                    "icolt_class": config.OTHER_ROW_LABEL,
                    "family": config.FAMILY_OTHER,
                    "ha": round(residuo_ha, 1),
                    "pct": round(100 * residuo_ha / agri_ha, 1) if agri_ha else 0.0,
                    "parcels": None,
                    "merged_classes": residuo_classi,
                }
            )

    # Quota della coltura dell'utente: solo se ha una classe iColt dedicata.
    if crop is not None:
        if crop["mappable"] and agri_ha > 0:
            crop_ha = float(
                agri.loc[
                    agri["crop_class"] == crop["icolt_class"], "ha_in_buffer"
                ].sum()
            )
            crop_pct = 100 * crop_ha / agri_ha
            crop["ha"] = round(crop_ha, 1)
            crop["pct_of_agri"] = round(crop_pct, 1)
            # Presenza nulla non e' "presenza limitata": va detta come assenza.
            crop["has_area"] = crop_ha > 0
        else:
            crop["ha"] = None
            crop["pct_of_agri"] = None
            crop["has_area"] = False

    return {
        "location": {"lat": lat, "lng": lng},
        "radius_m": int(radius_m),
        "dataset": {
            "source": config.DATASET_SOURCE,
            "year": config.DATASET_YEAR,
            "region": config.COVERAGE_REGION,
        },
        "buffer_ha": round(buffer_ha, 1),
        # `agri_ha` e' mantenuto per compatibilita' ma il nome e' improprio: il
        # layer ARPAE distribuito non contiene le classi non agricole, quindi
        # questa e' la superficie CARTOGRAFATA, non la superficie agricola.
        "agri_ha": round(agri_ha, 1),
        "mapped_ha": round(agri_ha, 1),
        "mapped_pct_of_buffer": round(100 * agri_ha / buffer_ha, 1)
        if buffer_ha
        else 0.0,
        "agri_pct_of_buffer": round(100 * agri_ha / buffer_ha, 1) if buffer_ha else 0.0,
        "parcels": int(len(agri)),
        "crop": crop,
        "coverage_note": coverage_note(harvest),
        "observability": observability(lat, lng),
        "composition": breakdown,
    }


def parcels_geojson(
    lat: float, lng: float, radius_m: float, harvest: Optional[str] = None
) -> Dict[str, Any]:
    """Particelle dentro il buffer, come GeoJSON, per il disegno sulla mappa.

    Le geometrie sono RITAGLIATE sul buffer e non semplificate: misurato, la
    semplificazione a ~10 m fa risparmiare solo il 15% dopo gzip introducendo
    fino al 5% di errore sulle superfici per classe, quindi non conviene. A 5 km
    il payload e' circa 0,2 MB compresso.
    """
    parcels, buffer_ha = analyze(lat, lng, radius_m, keep_clipped=True)
    crop = resolve_crop(harvest)
    target = crop["icolt_class"] if crop else None

    truncated = False
    features: List[Dict[str, Any]] = []
    if not parcels.empty:
        agri = parcels[parcels["is_agri"]].sort_values("ha_in_buffer", ascending=False)
        if len(agri) > config.MAX_PARCELS:
            agri = agri.head(config.MAX_PARCELS)
            truncated = True
        out = agri[["crop_class", "ha_in_buffer", "geometry"]].rename(
            columns={"crop_class": "icolt_class"}
        )
        out = out.assign(
            ha=out["ha_in_buffer"].round(2),
            is_crop=bool(target) and (out["icolt_class"] == target),
            family=out["icolt_class"].map(
                lambda c: config.CLASS_FAMILY.get(c, config.FAMILY_OTHER)
            ),
        ).drop(columns=["ha_in_buffer"])
        # Gli ettari sono gia' stati calcolati sulla geometria ESATTA qui sopra:
        # arrotondare le coordinate a 6 decimali (~11 cm) e' quindi puramente
        # cosmetico e non tocca nessun numero dichiarato. Misurato: circa meta'
        # del payload compresso. Il frontend non deve mai ricavare aree dalla
        # geometria ricevuta, altrimenti questo arrotondamento entrerebbe nelle
        # cifre mostrate.
        out = out.set_geometry(
            out.geometry.apply(lambda g: shapely.set_precision(g, 1e-6))
        )
        out = out[out.geometry.notna() & ~out.geometry.is_empty]
        # to_json() in un colpo solo: la serializzazione per riga e' ordini di
        # grandezza piu' lenta.
        features = json.loads(out.to_json(drop_id=True))["features"]

    return {
        "location": {"lat": lat, "lng": lng},
        "radius_m": int(radius_m),
        "dataset": {
            "source": config.DATASET_SOURCE,
            "year": config.DATASET_YEAR,
            "region": config.COVERAGE_REGION,
        },
        "buffer_ha": round(buffer_ha, 1),
        "buffer": json.loads(
            gpd.GeoSeries([buffer_polygon(lat, lng, radius_m)], crs=4326).to_json()
        )["features"][0]["geometry"],
        "crop": crop,
        "coverage_note": coverage_note(harvest),
        "observability": observability(lat, lng),
        "aggregated_classes": config.AGGREGATED_CLASSES,
        "count": len(features),
        "truncated": truncated,
        "parcels": {"type": "FeatureCollection", "features": features},
    }


def composition_with_sources(
    lat: float, lng: float, radius_m: float, harvest: Optional[str] = None
) -> Dict[str, Any]:
    """Composizione con AGREA come base e iColt come controllo indipendente.

    La scelta della sorgente principale non e' cosmetica. Misurato su 24 punti:
    AGREA copre piu' di iColt in 21, aderisce alle statistiche ufficiali al 97,6%
    della SAU censita contro il 74,1% di iColt, e sopra i 200 m di quota iColt e'
    semplicemente cieca. Quindi AGREA guida quando c'e'.

    iColt non si butta: e' l'unica fonte INDIPENDENTE per controllare AGREA, non ha
    bias dichiarativo e non ha soggetto. L'accordo geometrico fra le due e' circa
    l'80%, non il 100%: in pianura, dove esistono entrambe, quel disaccordo e'
    l'unica stima onesta dell'incertezza che possiamo mostrare.

    Se i file AGREA non sono sul volume, tutto ricade su iColt esattamente come
    prima: la funzione non si rompe mai per assenza del dato nuovo.
    """
    base_icolt = composition(lat, lng, radius_m, harvest)

    if not agrea.available():
        base_icolt["source"] = "icolt"
        base_icolt["crosscheck"] = None
        base_icolt["seminatural"] = None
        return base_icolt

    try:
        base_agrea = agrea.composition(lat, lng, radius_m, harvest)
        semi = agrea.seminatural(lat, lng, radius_m)
    except agrea.AgreaUnavailable as exc:
        logger_msg = str(exc)
        base_icolt["source"] = "icolt"
        base_icolt["crosscheck"] = None
        base_icolt["seminatural"] = None
        base_icolt["agrea_error"] = logger_msg
        return base_icolt

    # Nessun dato dichiarato nell'intorno: si resta su iColt invece di mostrare zeri.
    if base_agrea["agri_ha"] <= 0:
        base_icolt["source"] = "icolt"
        base_icolt["crosscheck"] = None
        base_icolt["seminatural"] = semi
        return base_icolt

    out = dict(base_agrea)
    out["source"] = "agrea"
    out["location"] = {"lat": lat, "lng": lng}
    out["radius_m"] = int(radius_m)
    out["dataset"] = {
        "source": config.AGREA_SOURCE,
        "year": config.AGREA_YEAR,
        "region": config.COVERAGE_REGION,
    }
    out["aggregated_classes"] = {}
    out["coverage_note"] = None  # la nota su vite e olivo riguarda iColt, non AGREA
    out["seminatural"] = semi
    out["observability"] = {
        "status": "full",
        "radius_m": int(radius_m),
        "mapped_pct": base_agrea["mapped_pct_of_buffer"],
        "quadrant_pct": [],
        "worst_quadrant_pct": None,
    }

    # Il controllo indipendente: cosa dice l'altra sorgente sulla stessa domanda.
    crop_agrea = (base_agrea.get("crop") or {}).get("pct_of_agri")
    crop_icolt = (base_icolt.get("crop") or {}).get("pct_of_agri")
    delta = (
        round(abs(crop_agrea - crop_icolt), 1)
        if crop_agrea is not None and crop_icolt is not None
        else None
    )
    out["crosscheck"] = {
        "source": "icolt",
        "year": config.DATASET_YEAR,
        "mapped_ha": base_icolt.get("mapped_ha"),
        "mapped_pct_of_buffer": base_icolt.get("mapped_pct_of_buffer"),
        "crop_pct_of_agri": crop_icolt,
        "crop_ha": (base_icolt.get("crop") or {}).get("ha"),
        "delta_pct_points": delta,
        # iColt e' cieca in collina: il suo silenzio non e' un disaccordo.
        "usable": base_icolt.get("observability", {}).get("status") != "suppressed",
        "coverage_note": base_icolt.get("coverage_note"),
    }
    return out
