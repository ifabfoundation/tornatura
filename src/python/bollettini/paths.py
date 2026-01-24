import os
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = Path(os.getenv("BOLLETTINI_RUNTIME_DIR", str(PACKAGE_DIR)))

DATA_DIR = PACKAGE_DIR / "data"
SHAPEFILE_DIR = DATA_DIR / "shapefiles"

OUTPUT_DIR = RUNTIME_DIR / "data" / "output"
OUTPUT_CIMICE_DIR = OUTPUT_DIR / "cimice"
OUTPUT_FLAVESCENZA_DIR = OUTPUT_DIR / "flavescenza"
