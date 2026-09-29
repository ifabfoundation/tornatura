"""Zone semi-naturali intorno a un punto: tutte le fonti, ogni ettaro contato una volta.

Sostituisce `agrea.seminatural`, che contava solo il bosco dichiarato e gli elementi AGREA. Le
categorie e l'ordine di priorita' delle fonti sono in config.py (`SEMINATURAL_*`); il ritaglio fra
le fonti e' gia' fatto dall'updater (modules/seminaturale_prepare.py), quindi qui si sommano
superfici che non si toccano:

  AGREA           appezzamenti con family "seminaturale" (bosco, siepi, margini dichiarati come
                  appezzamento), tara dei pascoli arborati, elementi del paesaggio (centroide nel
                  cerchio, come prima: scarto misurato 0-2%);
  strati          Carta forestale 2025 e Uso del suolo 2023 fuori da AGREA (poligoni ritagliati
                  esattamente sul cerchio);
  residuo SWF     pixel Copernicus di siepi e alberi che nessuna fonte vede (5 m, EPSG:3035).

Se gli strati o il raster mancano, la risposta e' quella del solo AGREA e lo dichiara (`layers`).
Misurato sui 33 punti dell'esperimento esperimenti/bosco_paesaggio/: 0,05 s di mediana, 2,7 s al
massimo a 10 km.
"""

import json
from typing import Any, Dict, List, Optional, Sequence

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from landscape import paths
from landscape.modules import agrea, config

CATEGORIE = list(config.SEMINATURAL_CATEGORIES)
CORE = [k for k, v in config.SEMINATURAL_CATEGORIES.items() if v["core"]]


def strati_available() -> bool:
    return paths.SEMINATURALE_STRATI_PARQUET.exists()


def swf_available() -> bool:
    return paths.SEMINATURALE_SWF_TIF.exists()


def _categoria_agrea(cls: pd.Series) -> pd.Series:
    """Categoria di un appezzamento o elemento AGREA semi-naturale (per nome di specie)."""
    return cls.astype(str).str.upper().map(config.SEMINATURAL_AGREA_CLS)


def _strati_nel_cerchio(metrico, path=None) -> gpd.GeoDataFrame:
    """Poligoni degli strati regionali ritagliati sul cerchio (in metri), con `ha_c`.

    Si ritagliano solo i poligoni che toccano il bordo: per quelli interi dentro il cerchio vale la
    superficie gia' calcolata dall'updater. A 10 km in collina sono ~9.000 poligoni e il ritaglio
    di tutti costava 1,4 s.
    """
    path = path or paths.SEMINATURALE_STRATI_PARQUET
    if not path.exists():
        return gpd.GeoDataFrame(
            {"categoria": [], "fonte": [], "ha_c": []},
            geometry=[],
            crs=config.METRIC_EPSG,
        )
    s = gpd.read_parquet(path, bbox=metrico.bounds)
    if s.empty:
        return s.assign(ha_c=[])
    s = s.iloc[s.sindex.query(metrico, predicate="intersects")].copy()
    interi = np.zeros(len(s), dtype=bool)
    interi[s.sindex.query(metrico, predicate="contains")] = True
    s["ha_c"] = s["ha"].values
    if (~interi).any():
        bordo = s.geometry.values[~interi]
        ritagliati = shapely.intersection(bordo, metrico)
        geo = s.geometry.values.copy()
        geo[~interi] = ritagliati
        s = s.set_geometry(gpd.GeoSeries(geo, index=s.index, crs=config.METRIC_EPSG))
        s.loc[~interi, "ha_c"] = shapely.area(ritagliati) / 10_000
    return s


def _swf_ha(metrico) -> Optional[float]:
    """Ettari di residuo Small Woody Features nel cerchio, o None se il raster non c'e'."""
    if not swf_available():
        return None
    import rasterio
    from rasterio import features
    from rasterio.windows import from_bounds

    cerchio = gpd.GeoSeries([metrico], crs=config.METRIC_EPSG).to_crs(3035).iloc[0]
    with rasterio.open(paths.SEMINATURALE_SWF_TIF) as src:
        finestra = (
            from_bounds(*cerchio.bounds, transform=src.transform)
            .round_offsets()
            .round_lengths()
        )
        dati = src.read(1, window=finestra, boundless=True, fill_value=0)
        t = src.window_transform(finestra)
    dentro = features.geometry_mask(
        [cerchio], out_shape=dati.shape, transform=t, invert=True
    )
    pixel_ha = abs(t.a * t.e) / 10_000
    return float((dati[dentro] == 1).sum() * pixel_ha)


def seminatural(lat: float, lng: float, radius_m: float) -> Dict[str, Any]:
    """Ettari per categoria e per fonte nel cerchio, piu' i totali per la pagina.

    Campi di prima, invariati nel significato per la pagina: `ha` e `pct_of_buffer` (ora la somma
    delle categorie `core`), `bosco_ha` (tutto il bosco, non piu' il solo dichiarato),
    `elementi_ha`/`elementi_n` (gli elementi AGREA). Nuovi: `categories`, `layers`, `sources`.
    """
    metrico, _, bbox = agrea._buffer(lat, lng, radius_m)
    buffer_ha = metrico.area / 10_000
    ha = {
        k: {"agrea": 0.0, "cf2025": 0.0, "us2023": 0.0, "swf2021": 0.0}
        for k in CATEGORIE
    }

    # --- AGREA: appezzamenti semi-naturali e tara dei pascoli arborati -----------------
    if agrea.available():
        g = agrea._leggi(paths.AGREA_COLTURE_PARQUET, bbox)
        if not g.empty:
            semi = g["family"].astype(str) == config.FAMILY_SEMINATURAL
            tara = g["cls"].astype(str).str.upper().isin(config.SEMINATURAL_AGREA_TARA)
            g = g[semi | tara]
        if not g.empty:
            ritagliati = (
                g.geometry.to_crs(config.METRIC_EPSG).make_valid().intersection(metrico)
            )
            g = g.assign(ha_c=ritagliati.area / 10_000)
            cls = g["cls"].astype(str).str.upper()
            e_semi = g["family"].astype(str) == config.FAMILY_SEMINATURAL
            cat = _categoria_agrea(g["cls"]).fillna(config.SEMINATURAL_AGREA_DEFAULT)
            for k, v in g[e_semi].groupby(cat[e_semi])["ha_c"].sum().items():
                ha[k]["agrea"] += float(v)
            for nome, quota in config.SEMINATURAL_AGREA_TARA.items():
                ha["arbusteti"]["agrea"] += float(
                    g.loc[cls == nome, "ha_c"].sum() * quota
                )

    # --- AGREA: elementi del paesaggio, per centroide -----------------------------------
    elementi_ha, elementi_n = 0.0, 0
    if agrea.elements_available():
        e = agrea._leggi(paths.AGREA_ELEMENTI_PARQUET, bbox)
        if not e.empty:
            dentro = e[e.geometry.to_crs(config.METRIC_EPSG).within(metrico)]
            elementi_ha = float(dentro["ha"].sum())
            elementi_n = int(len(dentro))
            cat = _categoria_agrea(dentro["cls"]).fillna(
                config.SEMINATURAL_ELEMENT_DEFAULT
            )
            for k, v in dentro.groupby(cat)["ha"].sum().items():
                ha[k]["agrea"] += float(v)

    # --- strati regionali, gia' fuori da AGREA ------------------------------------------
    s = _strati_nel_cerchio(metrico)
    if not s.empty:
        for (k, fonte), v in s.groupby(["categoria", "fonte"])["ha_c"].sum().items():
            ha[k][fonte] += float(v)

    # --- residuo Copernicus ---------------------------------------------------------------
    swf = _swf_ha(metrico)
    if swf is not None:
        ha[config.SEMINATURAL_SWF_CATEGORY]["swf2021"] += swf

    categories: List[Dict[str, Any]] = []
    for k in CATEGORIE:
        tot = sum(ha[k].values())
        categories.append(
            {
                "key": k,
                "label": config.SEMINATURAL_CATEGORIES[k]["label"],
                "core": config.SEMINATURAL_CATEGORIES[k]["core"],
                "ha": round(tot, 1),
                "pct_of_buffer": round(100 * tot / buffer_ha, 1) if buffer_ha else 0.0,
                "by_source": {f: round(v, 1) for f, v in ha[k].items() if v > 0.05},
            }
        )
    core_ha = sum(c["ha"] for c in categories if c["core"])
    usate = sorted({f for k in CATEGORIE for f, v in ha[k].items() if v > 0.05})
    return {
        "buffer_ha": round(buffer_ha, 1),
        "bosco_ha": round(sum(ha["bosco"].values()), 1),
        "elementi_ha": round(elementi_ha, 1),
        "elementi_n": elementi_n,
        "ha": round(core_ha, 1),
        "pct_of_buffer": round(100 * core_ha / buffer_ha, 1) if buffer_ha else 0.0,
        "categories": categories,
        "layers": {"regional": strati_available(), "swf": swf is not None},
        "sources": [
            {"id": f, "citation": config.SEMINATURAL_SOURCES[f]} for f in usate
        ],
        # L'approssimazione va dichiarata dove viene usata, non nascosta.
        "elementi_method": "centroide nel buffer (scarto misurato 0-2%)",
    }


def subtotal(block: Dict[str, Any], keys: Sequence[str]) -> Dict[str, Any]:
    """Somma di alcune categorie di un blocco `seminatural` (per i serbatoi di un organismo)."""
    scelte = [c for c in block.get("categories", []) if c["key"] in keys]
    tot = sum(c["ha"] for c in scelte)
    buffer_ha = block.get("buffer_ha") or 0.0
    return {
        "keys": [c["key"] for c in scelte],
        "ha": round(tot, 1),
        "pct_of_buffer": round(100 * tot / buffer_ha, 1) if buffer_ha else 0.0,
    }


def geometries(
    lat: float, lng: float, radius_m: float, keys: Sequence[str]
) -> gpd.GeoSeries:
    """Poligoni degli strati regionali di alcune categorie, in metri (per le distanze)."""
    metrico, _, _ = agrea._buffer(lat, lng, radius_m)
    if not strati_available():
        return gpd.GeoSeries([], crs=config.METRIC_EPSG)
    s = gpd.read_parquet(
        paths.SEMINATURALE_STRATI_PARQUET,
        bbox=metrico.bounds,
        columns=["categoria", "geometry"],
    )
    s = s[s["categoria"].isin(list(keys))]
    return (
        s.geometry.iloc[s.sindex.query(metrico, predicate="intersects")]
        if not s.empty
        else s.geometry
    )


def map_features(lat: float, lng: float, radius_m: float) -> Dict[str, Any]:
    """Feature GeoJSON degli strati regionali per la mappa, sopra la soglia di disegno.

    Dallo strato della mappa (poligoni uniti a celle di 5 km e semplificati dall'updater), non
    da quello dei conti. Stesse proprieta' degli appezzamenti AGREA (`icolt_class`, `family`,
    `ha`, `is_crop`) piu' `source_label`, che il popup scrive al posto di "AGREA" e che la mappa
    usa per non disegnarne il contorno. Tetto sui vertici: si tengono i poligoni piu' grandi, e
    `truncated` lo dice.
    """
    metrico, _, _ = agrea._buffer(lat, lng, radius_m)
    s = _strati_nel_cerchio(metrico, paths.SEMINATURALE_MAPPA_PARQUET)
    if s.empty:
        return {"features": [], "truncated": False}
    s = s[s["ha_c"] >= config.AGREA_MAP_MIN_HA].sort_values("ha_c", ascending=False)
    abitato = (s["categoria"] == "abitato").values
    entro = np.zeros(len(s), dtype=bool)
    for gruppo, tetto in (
        (~abitato, config.SEMINATURAL_MAP_VERTEX_BUDGET),
        (abitato, config.SEMINATURAL_MAP_ABITATO_VERTEX_BUDGET),
    ):
        vertici = shapely.get_num_coordinates(s.geometry.values[gruppo])
        entro[np.flatnonzero(gruppo)] = np.cumsum(vertici) <= tetto
    truncated = bool((~entro).any())
    s = s[entro]
    if s.empty:
        return {"features": [], "truncated": truncated}
    etichetta_fonte = {
        "cf2025": "Carta forestale regionale 2025",
        "us2023": "Uso del suolo 2023",
    }
    out = gpd.GeoDataFrame(
        {
            "icolt_class": s["categoria"]
            .map(lambda k: config.SEMINATURAL_CATEGORIES[k]["label"])
            .values,
            "declared": "",
            "harvest_code": None,
            "family": s["categoria"]
            .map(
                lambda k: config.SEMINATURAL_MAP_FAMILY.get(
                    k, config.FAMILY_SEMINATURAL
                )
            )
            .values,
            "ha": s["ha_c"].round(2).values,
            "is_crop": False,
            "source_label": s["fonte"].map(etichetta_fonte).values,
        },
        geometry=gpd.GeoSeries(s.geometry.values, crs=config.METRIC_EPSG)
        .to_crs(4326)
        .values,
        crs=4326,
    )
    features = json.loads(out.to_json(drop_id=True))["features"]
    for f in features:
        f["geometry"]["coordinates"] = agrea._coordinate_arrotondate(
            f["geometry"]["coordinates"], config.SEMINATURAL_MAP_DECIMALS
        )
    return {"features": features, "truncated": truncated}


def swf_image(lat: float, lng: float, radius_m: float) -> Dict[str, Any]:
    """Il residuo Copernicus nel cerchio come immagine per la mappa.

    PNG trasparente riproiettato in EPSG:3857 (vicino piu' prossimo), con i quattro angoli in
    gradi per la sorgente `image` di Mapbox: in EPSG:3857 l'immagine e' allineata ai meridiani e
    i pixel cadono dove devono (nel 3035 del raster l'asse nord ruota di circa un grado, cioe'
    ~90 m di errore al bordo di un cerchio di 5 km).
    """
    if not swf_available():
        return {"available": False}
    import base64

    import rasterio
    from rasterio import features
    from rasterio.io import MemoryFile
    from rasterio.transform import from_origin
    from rasterio.warp import Resampling, reproject

    metrico, _, _ = agrea._buffer(lat, lng, radius_m)
    cerchio = gpd.GeoSeries([metrico], crs=config.METRIC_EPSG).to_crs(3857).iloc[0]
    x0, y0, x1, y1 = cerchio.bounds
    # 5 m a terra: in EPSG:3857 un metro vale 1/cos(lat) unita'
    px = 5.0 / np.cos(np.radians(lat))
    w = int(np.ceil((x1 - x0) / px))
    h = int(np.ceil((y1 - y0) / px))
    dst_t = from_origin(x0, y1, px, px)
    dst = np.zeros((h, w), dtype="uint8")
    with rasterio.open(paths.SEMINATURALE_SWF_TIF) as src:
        reproject(
            source=rasterio.band(src, 1),
            destination=dst,
            dst_transform=dst_t,
            dst_crs="EPSG:3857",
            resampling=Resampling.nearest,
        )
    dentro = features.geometry_mask(
        [cerchio], out_shape=(h, w), transform=dst_t, invert=True
    )
    pieno = (dst == 1) & dentro
    rgba = np.zeros((4, h, w), dtype="uint8")
    for banda, valore in enumerate(config.SEMINATURAL_SWF_IMAGE_RGBA):
        rgba[banda][pieno] = valore
    with MemoryFile() as mem:
        with mem.open(driver="PNG", width=w, height=h, count=4, dtype="uint8") as png:
            png.write(rgba)
        dati = mem.read()
    angoli = gpd.GeoSeries(
        gpd.points_from_xy([x0, x1, x1, x0], [y1, y1, y0, y0]), crs=3857
    ).to_crs(4326)
    return {
        "available": True,
        # ordine di Mapbox: alto-sinistra, alto-destra, basso-destra, basso-sinistra
        "coordinates": [[round(p.x, 7), round(p.y, 7)] for p in angoli],
        "image": "data:image/png;base64," + base64.b64encode(dati).decode("ascii"),
        "source": config.SEMINATURAL_SOURCES["swf2021"],
    }
