import logging
import os
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
import pandas as pd
from pydantic import BaseModel, Field, conint
import uvicorn

from peronospora.inference_service import run_inference_pipeline
from peronospora import paths


logger = logging.getLogger("peronospora_api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

app = FastAPI(title="Peronospora Inference API", version="1.0.0")


@app.get("/health")
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
    return value.strip().lower().replace(" ", "_")


def _load_predictions(lead: int) -> pd.DataFrame:
    path = paths.PREDICTIONS_DIR / f"lead_{lead}.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Predictions not found: {path}")
    return pd.read_csv(path)


@app.get("/api/risk/current")
def risk_current() -> Dict[str, Any]:
    df = _load_predictions(0)
    return _format_predictions(df)


@app.get("/api/risk/forecast")
def risk_forecast() -> Dict[str, Any]:
    df = _load_predictions(1)
    return _format_predictions(df)


@app.get("/api/risk/province/{province}")
def risk_by_province(
    province: str,
    lead: int = Query(default=0, ge=0, le=1),
) -> Dict[str, Any]:
    df = _load_predictions(lead)
    normalized = _normalize_province(province)
    df = df[df["NUTS_3"].astype(str).str.lower() == normalized]
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Province not found: {province}")

    payload = _format_predictions(df)
    payload["province"] = normalized
    payload["lead"] = lead
    return payload


@app.get("/api/risk/history")
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


@app.get("/api/weather/forecast/{province}")
def weather_forecast(province: str) -> FileResponse:
    file_path = paths.FORECAST_DIR / f"{province}_forecast.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Forecast not found: {file_path}")
    return FileResponse(file_path, media_type="text/csv")


@app.get("/api/map")
def risk_map() -> FileResponse:
    if not paths.RISK_MAP_PATH.exists():
        raise HTTPException(status_code=404, detail=f"Map not found: {paths.RISK_MAP_PATH}")
    return FileResponse(paths.RISK_MAP_PATH, media_type="text/html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
