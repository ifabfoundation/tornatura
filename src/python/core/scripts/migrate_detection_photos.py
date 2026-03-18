#!/usr/bin/env python3
"""
Wrap legacy detectionData.photos FileInfo entries into detectionPhoto objects.
"""
from __future__ import annotations

import argparse
import sys

from mongoengine import connect

from core.config import APIConfig
from core.models import DetectionModel


def connect_db():
    connect(
        host=APIConfig.MONGO_DATABASE_HOST,
        port=27017,
        username=APIConfig.MONGO_USER,
        password=APIConfig.MONGO_PASSWORD,
    )


def is_legacy_photo(photo: object) -> bool:
    return (
        isinstance(photo, dict)
        and "category" in photo
        and "name" in photo
        and "photo" not in photo
    )


def is_new_photo(photo: object) -> bool:
    return isinstance(photo, dict) and isinstance(photo.get("photo"), dict)


def migrate_detection_photos(dry_run: bool) -> int:
    collection = DetectionModel._get_collection()
    converted = 0
    skipped = 0
    invalid = 0

    for detection in collection.find({}, {"detectionData.photos": 1}):
        detection_data = detection.get("detectionData") or {}
        photos = detection_data.get("photos") or []

        if not photos:
            skipped += 1
            continue

        if all(is_new_photo(photo) for photo in photos):
            skipped += 1
            continue

        if not all(is_legacy_photo(photo) for photo in photos):
            invalid += 1
            continue

        migrated_photos = [
            {
                "caption": "",
                "photo": {
                    "category": photo["category"],
                    "name": photo["name"],
                },
                "position": None,
            }
            for photo in photos
        ]

        if not dry_run:
            collection.update_one(
                {"_id": detection["_id"]},
                {"$set": {"detectionData.photos": migrated_photos}},
            )
        converted += 1

    print(
        f"Detection photo migration: converted={converted}, skipped={skipped}, invalid={invalid}"
    )
    return 0 if invalid == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate detectionData.photos from FileInfo[] to detectionPhoto[]."
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes.")
    args = parser.parse_args()

    connect_db()
    return migrate_detection_photos(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
