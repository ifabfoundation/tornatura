#!/usr/bin/env python3
"""
Generate provinces_italy.json from openpolis GeoJSON.

Downloads the Italian provinces GeoJSON, extracts province info
(slug, display name, bounding box, abbreviation, region) and saves
as a JSON config file used by the inference pipeline.

Run once (data is static):
    python generate_provinces_config.py
"""

import json
import re
import unicodedata
from pathlib import Path

import geopandas as gpd
from peronospora import paths

SCRIPT_DIR = paths.DATA_DIR
OUTPUT_FILE = SCRIPT_DIR / "provinces_italy.json"
GEOJSON_URL = "https://github.com/openpolis/geojson-italy/raw/master/geojson/limits_IT_provinces.geojson"


def slugify(name: str) -> str:
    """Convert province name to filesystem-safe slug."""
    s = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    s = s.lower()
    # Replace hyphens, slashes, and apostrophes with underscore (preserves word boundaries)
    s = re.sub(r"[-/''`]", '_', s)
    s = re.sub(r'[^a-z0-9\s_]', '', s)
    s = re.sub(r'\s+', '_', s.strip())
    s = re.sub(r'_+', '_', s)
    return s


def main():
    print(f"Downloading GeoJSON from {GEOJSON_URL}...")
    gdf = gpd.read_file(GEOJSON_URL)
    print(f"Found {len(gdf)} provinces")

    provinces = {}

    for _, row in gdf.iterrows():
        name = row['prov_name']
        slug = slugify(name)
        bounds = row.geometry.bounds  # (minx, miny, maxx, maxy) = (lon_min, lat_min, lon_max, lat_max)

        provinces[slug] = {
            "display_name": name,
            "prov_acr": row['prov_acr'],
            "reg_name": row['reg_name'],
            "bbox": [
                round(bounds[0], 4),
                round(bounds[1], 4),
                round(bounds[2], 4),
                round(bounds[3], 4)
            ]
        }

    # Sort by slug for readability
    provinces = dict(sorted(provinces.items()))

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(provinces, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(provinces)} provinces to {OUTPUT_FILE}")

    # Verify no duplicate slugs
    slugs = list(provinces.keys())
    if len(slugs) != len(set(slugs)):
        dupes = [s for s in slugs if slugs.count(s) > 1]
        print(f"WARNING: Duplicate slugs found: {set(dupes)}")
    else:
        print("No duplicate slugs")


if __name__ == "__main__":
    main()
