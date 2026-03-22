import logging
import json
import os
import re
import threading
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import geopandas as gpd
import pandas as pd
from pydantic import BaseModel, Field, conint
from shapely.geometry import Point
import uvicorn

from peronospora import paths


logger = logging.getLogger("peronospora_api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

app = FastAPI(title="Peronospora Inference API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
_PROVINCE_GDF: Optional[gpd.GeoDataFrame] = None
_RISK_LEVELS: Optional[Dict[str, Any]] = None


@app.get("/v1/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid date: {value}") from exc


def _format_predictions(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {"forecast_date": None, "target_week": None, "provinces": []}

    df = _enrich_prediction_rows(df)
    df = df.where(pd.notnull(df), None)
    return {
        "forecast_date": df["forecast_base"].iloc[0],
        "target_week": {
            "start": df["target_period_start"].iloc[0],
            "end": df["target_period_end"].iloc[0],
        },
        "provinces": df.to_dict(orient="records"),
    }


def _normalize_province(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return normalized


def _load_risk_levels() -> Dict[str, Any]:
    global _RISK_LEVELS
    if _RISK_LEVELS is not None:
        return _RISK_LEVELS

    risk_levels_path = paths.PACKAGE_DIR / "risk_levels.json"
    if not risk_levels_path.exists():
        raise HTTPException(status_code=500, detail=f"Risk levels file not found: {risk_levels_path}")

    with risk_levels_path.open(encoding="utf-8") as f:
        _RISK_LEVELS = json.load(f)

    return _RISK_LEVELS


def _normalize_risk_level(value: Any) -> Optional[str]:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _enrich_prediction_rows(df: pd.DataFrame) -> pd.DataFrame:
    if "risk_level" not in df.columns:
        return df

    risk_levels = _load_risk_levels()
    df = df.copy()
    df["risk_meta"] = df["risk_level"].apply(
        lambda value: risk_levels.get(_normalize_risk_level(value))
    )
    return df


def _load_province_shapefile() -> gpd.GeoDataFrame:
    global _PROVINCE_GDF
    if _PROVINCE_GDF is not None:
        return _PROVINCE_GDF

    shapefile_candidates = (
        paths.STATIC_DATA_DIR / "weather" / "shapefiles" / "province_italia.shp",
    )

    shapefile_path = next((path for path in shapefile_candidates if path.exists()), None)
    if shapefile_path is None:
        raise HTTPException(status_code=500, detail="Province shapefile not found")

    gdf = gpd.read_file(shapefile_path)

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
    gdf = _load_province_shapefile()
    point = Point(lng, lat)
    matches = gdf[gdf.geometry.intersects(point)]
    if matches.empty:
        return None
    province_name = str(matches.iloc[0]["province_name"])
    return _normalize_province(province_name)


def _load_predictions(lead: int) -> pd.DataFrame:
    path = paths.PREDICTIONS_DIR / f"lead_{lead}.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Predictions not found: {path}")
    return pd.read_csv(path)


@app.get("/v1/peronospora/risk/current")
def risk_current() -> Dict[str, Any]:
    df = _load_predictions(0)
    return _format_predictions(df)


@app.get("/v1/peronospora/risk/forecast")
def risk_forecast() -> Dict[str, Any]:
    df = _load_predictions(1)
    return _format_predictions(df)


def _risk_by_province(province: str, lead: int) -> Dict[str, Any]:
    df = _load_predictions(lead)
    normalized = _normalize_province(province)
    df = df[df["NUTS_3"].astype(str).str.lower() == normalized]
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Province not found: {province}")

    payload = _format_predictions(df)
    payload["province"] = normalized
    return payload


@app.get("/v1/peronospora/risk/province/{province}/current")
def risk_by_province_current(province: str) -> Dict[str, Any]:
    return _risk_by_province(province, lead=0)


@app.get("/v1/peronospora/risk/province/{province}/forecast")
def risk_by_province_forecast(province: str) -> Dict[str, Any]:
    return _risk_by_province(province, lead=1)


@app.get("/v1/peronospora/risk/history")
def risk_history(
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
) -> Dict[str, List[Dict[str, Any]]]:
    start_dt = _parse_date(start)
    end_dt = _parse_date(end)

    if start_dt and end_dt and start_dt > end_dt:
        raise HTTPException(status_code=400, detail="start must be before end")

    if not paths.PREDICTIONS_HISTORY_DIR.exists():
        raise HTTPException(
            status_code=404,
            detail=f"History directory not found: {paths.PREDICTIONS_HISTORY_DIR}",
        )

    results: List[Dict[str, Any]] = []
    for file_path in sorted(paths.PREDICTIONS_HISTORY_DIR.glob("*.csv")):
        name = file_path.stem
        if "_lead_" not in name:
            continue
        try:
            date_part, lead_part = name.split("_lead_", 1)
            forecast_date = datetime.fromisoformat(date_part)
        except ValueError:
            continue

        if start_dt and forecast_date < start_dt:
            continue
        if end_dt and forecast_date > end_dt:
            continue

        df = pd.read_csv(file_path)
        payload = _format_predictions(df)
        payload["lead"] = int(lead_part) if lead_part.isdigit() else lead_part
        results.append(payload)

    return {"results": results}


@app.get("/v1/weather/forecast/{province}")
def weather_forecast(province: str) -> Dict[str, Any]:
    normalized = _normalize_province(province)
    file_path = paths.FORECAST_DIR / f"{normalized}_forecast.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Forecast not found: {file_path}")

    df = pd.read_csv(file_path)
    df = df.where(pd.notnull(df), None)
    forecast_base = df["forecast_base"].iloc[0] if not df.empty else None
    return {
        "province": normalized,
        "forecast_base": forecast_base,
        "data": df.to_dict(orient="records"),
    }


def _risk_by_location(lat: float, lng: float, lead: int) -> Dict[str, Any]:
    province = _province_from_point(lat, lng)
    if not province:
        raise HTTPException(status_code=404, detail="Location not in an Italian province")

    df = _load_predictions(lead)
    df = df[df["NUTS_3"].astype(str).str.lower() == province]
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Prediction not found for province: {province}")

    df = _enrich_prediction_rows(df)
    row = df.where(pd.notnull(df), None).to_dict(orient="records")[0]
    return {
        "forecast_date": row.get("forecast_base"),
        "target_week": {
            "start": row.get("target_period_start"),
            "end": row.get("target_period_end"),
        },
        "detail": row,
        "location": {"lat": lat, "lng": lng},
        "province": province,
    }


@app.get("/v1/peronospora/risk/location/current")
def risk_location_current(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
) -> Dict[str, Any]:
    return _risk_by_location(lat, lng, lead=0)


@app.get("/v1/peronospora/risk/location/forecast")
def risk_location_forecast(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
) -> Dict[str, Any]:
    return _risk_by_location(lat, lng, lead=1)


@app.get("/v1/peronospora/risk/map")
def risk_map() -> FileResponse:
    if not paths.RISK_MAP_PATH.exists():
        raise HTTPException(status_code=404, detail=f"Map not found: {paths.RISK_MAP_PATH}")
    return FileResponse(paths.RISK_MAP_PATH, media_type="text/html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
