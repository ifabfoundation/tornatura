import os
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = Path(os.getenv("PERONOSPORA_RUNTIME_DIR", str(PACKAGE_DIR)))

STATIC_DATA_DIR = Path(os.getenv("PERONOSPORA_STATIC_DATA_DIR", str(PACKAGE_DIR / "data")))
MODEL_DIR = Path(os.getenv("PERONOSPORA_MODEL_DIR", str(PACKAGE_DIR / "model")))

DATA_DIR = RUNTIME_DIR / "data"
WEATHER_DIR = DATA_DIR / "weather"
FORECAST_DIR = WEATHER_DIR / "forecast"
CACHE_DIR = WEATHER_DIR / "cache"
CACHE_HOURLY_DIR = CACHE_DIR / "hourly"
CACHE_DAILY_DIR = CACHE_DIR / "daily"
TEMP_DIR = WEATHER_DIR / "temp_grib"
PHENOLOGY_CSV_DIR = DATA_DIR / "phenology" / "phenology_csv"
INFERENCE_DIR = DATA_DIR / "dataframe_inference"

PREDICTIONS_DIR = RUNTIME_DIR / "predictions"
PREDICTIONS_HISTORY_DIR = PREDICTIONS_DIR / "history"
RISK_MAP_PATH = RUNTIME_DIR / "risk_map_satellite.html"
