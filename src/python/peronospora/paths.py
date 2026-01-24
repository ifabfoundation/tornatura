import os
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = Path(os.getenv("PERONOSPORA_RUNTIME_DIR", str(PACKAGE_DIR)))

STATIC_DATA_DIR = Path(str(PACKAGE_DIR / "data"))
MODEL_DIR = Path(str(PACKAGE_DIR / "model"))

DATA_DIR = PACKAGE_DIR / "data"
PHENOLOGY_CSV_DIR = DATA_DIR / "phenology" / "phenology_csv"
INFERENCE_DIR = DATA_DIR / "dataframe_inference"

WEATHER_DIR = RUNTIME_DIR / "weather"
FORECAST_DIR = WEATHER_DIR / "forecast"
CACHE_DIR = WEATHER_DIR / "cache"
CACHE_HOURLY_DIR = CACHE_DIR / "hourly"
CACHE_DAILY_DIR = CACHE_DIR / "daily"
TEMP_DIR = WEATHER_DIR / "temp_grib"

PREDICTIONS_DIR = RUNTIME_DIR / "predictions"
PREDICTIONS_HISTORY_DIR = PREDICTIONS_DIR / "history"
RISK_MAP_PATH = RUNTIME_DIR / "risk_map_satellite.html"

_DIRS_TO_CREATE = (
    RUNTIME_DIR,
    STATIC_DATA_DIR,
    MODEL_DIR,
    DATA_DIR,
    WEATHER_DIR,
    FORECAST_DIR,
    CACHE_DIR,
    CACHE_HOURLY_DIR,
    CACHE_DAILY_DIR,
    TEMP_DIR,
    PHENOLOGY_CSV_DIR,
    INFERENCE_DIR,
    PREDICTIONS_DIR,
    PREDICTIONS_HISTORY_DIR,
)

for _path in _DIRS_TO_CREATE:
    _path.mkdir(parents=True, exist_ok=True)
