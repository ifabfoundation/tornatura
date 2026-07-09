import logging
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import geopandas as gpd
from shapely.geometry import Point
import uvicorn

from bollettini import paths
from bollettini.modules.config import COLTURE, REGIONI


logger = logging.getLogger("bollettini_api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

app = FastAPI(title="Bollettini API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_PROVINCE_GDF: Optional[gpd.GeoDataFrame] = None

_REGION_ID_BY_CODE = {
    "8": "emilia_romagna",
    "08": "emilia_romagna",
    "15": "campania",
}

_REPORT_SLUG_CANDIDATES_BY_REGION_AND_PROVINCE = {
    "emilia_romagna": {
        "bologna": ["bologna_ferrara"],
        "ferrara": ["bologna_ferrara"],
        "forli_cesena": ["forli_cesena_ravenna_rimini"],
        "ravenna": ["forli_cesena_ravenna_rimini"],
        "rimini": ["forli_cesena_ravenna_rimini"],
        "modena": ["modena"],
        "reggio_nell_emilia": ["reggio_emilia"],
        "reggio_emilia": ["reggio_emilia"],
        "parma": ["parma"],
        "piacenza": ["piacenza"],
    },
    "campania": {
        "avellino": ["av"],
        "benevento": ["bn"],
        "caserta": ["ce"],
        "napoli": ["na"],
        "salerno": ["sa"],
    },
}

_ITALY_PROVINCE_NAME_COLUMNS = ("province_name", "prov_name", "DEN_UTS", "NAME", "name")
_ITALY_REGION_NAME_COLUMNS = ("region_name", "regione", "REGIONE", "COD_REG", "NUTS1")


@app.get("/v1/bollettini/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return normalized


def _normalize_culture_id(value: str) -> Optional[str]:
    normalized = _normalize_text(value).upper()
    if normalized in COLTURE:
        return normalized
    for culture_id, culture_data in COLTURE.items():
        if _normalize_text(culture_data["nome"]).upper() == normalized:
            return culture_id
    return None


def _report_slug_candidates(region_id: str, province_name: str) -> list[str]:
    normalized_province = _normalize_text(province_name)
    candidates = _REPORT_SLUG_CANDIDATES_BY_REGION_AND_PROVINCE.get(region_id, {}).get(
        normalized_province,
        [],
    )
    if candidates:
        return candidates
    return [normalized_province]


def _shapefile_candidates() -> list[Path]:
    local_shapefile = paths.SHAPEFILE_DIR / "province_emilia_romagna.shp"
    italy_shapefile = paths.SHAPEFILE_DIR / "province_italia.shp"
        
    # Prefer the all-Italy shapefile so lat/lng in Campania (and other regions)
    # resolve too; fall back to the Emilia-Romagna-only shapefile if it is absent.
    return [italy_shapefile, local_shapefile]


def _rename_first_matching_column(gdf: gpd.GeoDataFrame, candidates: tuple[str, ...], target: str) -> gpd.GeoDataFrame:
    if target in gdf.columns:
        return gdf
    for candidate in candidates:
        if candidate in gdf.columns:
            return gdf.rename(columns={candidate: target})
    return gdf


def _load_emilia_romagna_shapefile() -> gpd.GeoDataFrame:
    global _PROVINCE_GDF
    if _PROVINCE_GDF is not None:
        return _PROVINCE_GDF

    for shapefile in _shapefile_candidates():
        if shapefile.exists():
            gdf = gpd.read_file(shapefile)
            break
    else:
        raise HTTPException(status_code=500, detail="Province shapefile not found")

    gdf = _rename_first_matching_column(gdf, _ITALY_PROVINCE_NAME_COLUMNS, "province_name")
    gdf = _rename_first_matching_column(gdf, _ITALY_REGION_NAME_COLUMNS, "region_name")

    if "province_name" not in gdf.columns:
        raise HTTPException(status_code=500, detail="Province shapefile missing province_name column")

    if "region_name" not in gdf.columns:
        gdf["region_name"] = ""

    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    _PROVINCE_GDF = gdf
    return gdf


def _location_from_point(lat: float, lng: float) -> Optional[Dict[str, str]]:
    gdf = _load_emilia_romagna_shapefile()
    point = Point(lng, lat)
    matches = gdf[gdf.geometry.intersects(point)]
    if matches.empty:
        return None
    match = matches.iloc[0]
    return {
        "province_name": str(match["province_name"]),
        "region_name": str(match.get("region_name", "")),
    }


def _parse_date_from_filename(filename: str) -> Optional[datetime]:
    match = re.search(r"(\d{2}-\d{2}-\d{4})", filename)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%d-%m-%Y")
    except ValueError:
        return None


def _region_id_from_name(region_name: str, province_name: str) -> Optional[str]:
    normalized_region = _normalize_text(region_name)
    if normalized_region in _REGION_ID_BY_CODE:
        return _REGION_ID_BY_CODE[normalized_region]
    for region_id, region_data in REGIONI.items():
        if _normalize_text(region_data["nome"]) == normalized_region:
            return region_id
    normalized_province = _normalize_text(province_name)
    for region_id, province_map in _REPORT_SLUG_CANDIDATES_BY_REGION_AND_PROVINCE.items():
        if normalized_province in province_map:
            return region_id
    return None


def _latest_colture_report_path(culture_id: str, region_id: str, province_name: str) -> tuple[Path, str]:
    culture_dir = paths.OUTPUT_DIR / region_id / culture_id.lower()
    if not culture_dir.exists():
        raise HTTPException(status_code=404, detail="Culture reports not found")

    candidate_paths: list[tuple[Path, str]] = []
    for slug in _report_slug_candidates(region_id, province_name):
        files = list(culture_dir.glob(f"{slug}_*.md"))
        candidate_paths.extend((path, slug) for path in files)

    if not candidate_paths:
        raise HTTPException(status_code=404, detail="Culture report not available for province")

    def sort_key(item: tuple[Path, str]):
        path, _ = item
        date_value = _parse_date_from_filename(path.name)
        return date_value or datetime.fromtimestamp(path.stat().st_mtime)

    return max(candidate_paths, key=sort_key)


def _load_colture_report(culture_id: str, lat: float, lng: float) -> Dict[str, Any]:
    location = _location_from_point(lat, lng)
    if not location:
        raise HTTPException(status_code=404, detail="Location not in supported province")

    province_name = location["province_name"]
    region_id = _region_id_from_name(location.get("region_name", ""), province_name)
    if not region_id:
        raise HTTPException(status_code=404, detail="Region not supported for culture reports")

    report_path, report_slug = _latest_colture_report_path(culture_id, region_id, province_name)
    content_md = report_path.read_text(encoding="utf-8")
    report_date = _parse_date_from_filename(report_path.name)
    if report_date is None:
        report_date = datetime.fromtimestamp(report_path.stat().st_mtime)

    return {
        "type": "culture",
        "culture": culture_id.lower(),
        "region": region_id,
        "province": province_name,
        "report_slug": report_slug,
        "filename": report_path.name,
        "report_date": report_date.date().isoformat(),
        "last_modified": datetime.fromtimestamp(report_path.stat().st_mtime).isoformat(),
        "content": content_md,
        "location": {"lat": lat, "lng": lng},
    }

@app.get("/v1/bollettini/culture/{culture}/location")
def culture_by_location(
    culture: str,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
) -> Dict[str, Any]:
    culture_id = _normalize_culture_id(culture)
    if not culture_id:
        raise HTTPException(status_code=400, detail="Invalid culture")
    return _load_colture_report(culture_id, lat, lng)


if __name__ == "__main__":
    host = os.getenv("BOLLETTINI_API_HOST", "0.0.0.0")
    port = int(os.getenv("BOLLETTINI_API_PORT", "8080"))
    uvicorn.run(app, host=host, port=port, log_level="info")
