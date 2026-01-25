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

_REPORT_SLUG_BY_PROVINCE = {
    "bologna": "bologna_ferrara",
    "ferrara": "bologna_ferrara",
    "forli_cesena": "forli_cesena_ravenna_rimini",
    "ravenna": "forli_cesena_ravenna_rimini",
    "rimini": "forli_cesena_ravenna_rimini",
    "modena": "modena",
    "reggio_nell_emilia": "reggio_emilia",
    "reggio_emilia": "reggio_emilia",
    "parma": "parma",
    "piacenza": "piacenza",
}


@app.get("/v1/bollettini/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return normalized


def _report_slug_from_province_name(name: str) -> Optional[str]:
    normalized = _normalize_text(name)
    return _REPORT_SLUG_BY_PROVINCE.get(normalized)


def _shapefile_candidates() -> list[Path]:
    local_shapefile = paths.SHAPEFILE_DIR / "province_emilia_romagna.shp"
    peronospora_shapefile = (
        Path(__file__).resolve().parent.parent
        / "peronospora"
        / "weather"
        / "shapefiles"
        / "province_emilia_romagna.shp"
    )
    return [local_shapefile, peronospora_shapefile]


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

    if "prov_name" in gdf.columns:
        gdf = gdf.rename(columns={"prov_name": "province_name"})
    elif "DEN_UTS" in gdf.columns:
        gdf = gdf.rename(columns={"DEN_UTS": "province_name"})

    if "province_name" not in gdf.columns:
        raise HTTPException(status_code=500, detail="Province shapefile missing province_name column")

    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    _PROVINCE_GDF = gdf
    return gdf


def _province_from_point(lat: float, lng: float) -> Optional[str]:
    gdf = _load_emilia_romagna_shapefile()
    point = Point(lng, lat)
    matches = gdf[gdf.geometry.intersects(point)]
    if matches.empty:
        return None
    return str(matches.iloc[0]["province_name"])


def _parse_date_from_filename(filename: str) -> Optional[datetime]:
    match = re.search(r"(\d{2}-\d{2}-\d{4})", filename)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%d-%m-%Y")
    except ValueError:
        return None


def _latest_report_path(report_type: str, report_slug: str) -> Path:
    if report_type == "cimice":
        output_dir = paths.OUTPUT_CIMICE_DIR
    elif report_type == "flavescenza":
        output_dir = paths.OUTPUT_FLAVESCENZA_DIR
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")

    files = list(output_dir.glob(f"{report_slug}_*.md"))
    if not files:
        raise HTTPException(status_code=404, detail="Report not found")

    def sort_key(path: Path):
        date_value = _parse_date_from_filename(path.name)
        return (date_value or datetime.fromtimestamp(path.stat().st_mtime))

    return max(files, key=sort_key)


def _load_report(report_type: str, report_slug: str) -> Dict[str, Any]:
    report_path = _latest_report_path(report_type, report_slug)
    content_md = report_path.read_text(encoding="utf-8")
    report_date = _parse_date_from_filename(report_path.name)
    if report_date is None:
        report_date = datetime.fromtimestamp(report_path.stat().st_mtime)
    return {
        "type": report_type,
        "province": report_slug,
        "filename": report_path.name,
        "report_date": report_date.date().isoformat(),
        "last_modified": datetime.fromtimestamp(report_path.stat().st_mtime).isoformat(),
        "content": content_md,
    }


def _report_for_location(report_type: str, lat: float, lng: float) -> Dict[str, Any]:
    province_name = _province_from_point(lat, lng)
    if not province_name:
        raise HTTPException(status_code=404, detail="Location not in Emilia-Romagna province")

    report_slug = _report_slug_from_province_name(province_name)
    if not report_slug:
        raise HTTPException(status_code=404, detail="Report not available for province")

    payload = _load_report(report_type, report_slug)
    payload["location"] = {"lat": lat, "lng": lng}
    return payload


@app.get("/v1/bollettini/cimice/location")
def cimice_by_location(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
) -> Dict[str, Any]:
    return _report_for_location("cimice", lat, lng)


@app.get("/v1/bollettini/flavescenza/location")
def flavescenza_by_location(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
) -> Dict[str, Any]:
    return _report_for_location("flavescenza", lat, lng)


if __name__ == "__main__":
    host = os.getenv("BOLLETTINI_API_HOST", "0.0.0.0")
    port = int(os.getenv("BOLLETTINI_API_PORT", "8080"))
    uvicorn.run(app, host=host, port=port, log_level="info")
