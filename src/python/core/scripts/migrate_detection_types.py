#!/usr/bin/env python3
"""
Migrate DetectionType documents to use observationTypeId, remove legacy typology/method,
and backfill ObservationType fields from legacy detection_texts.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict

from mongoengine import connect

from core.config import APIConfig
from core.models import ObservationType


def connect_db():
    connect(
        host=APIConfig.MONGO_DATABASE_HOST,
        port=27017,
        username=APIConfig.MONGO_USER,
        password=APIConfig.MONGO_PASSWORD,
    )


def load_detection_texts():
    """Return detection text docs from legacy collection if present."""
    db = ObservationType._get_db()  # Uses the active connection
    if "detection_text" not in db.list_collection_names():
        return []
    return list(db["detection_text"].find({}))


def build_observation_map():
    mapping = defaultdict(list)
    for obs in ObservationType.objects():
        key = (obs.typology.lower(), obs.method.lower())
        mapping[key].append(obs)
    return mapping


def migrate_detection_types(dry_run: bool) -> int:
    mapping = build_observation_map()
    updated = 0
    skipped = 0
    ambiguous = 0
    db = ObservationType._get_db()
    detection_collection = db["detection_type"]

    for det in detection_collection.find({}):
        updates_set = {}
        updates_unset = {}

        has_observation_type = bool(det.get("observationTypeId"))
        typology = det.get("typology")
        method = det.get("method")

        if not has_observation_type:
            if not typology or not method:
                skipped += 1
                continue

            matches = mapping.get((typology.lower(), method.lower()), [])
            if len(matches) != 1:
                ambiguous += 1
                continue

            updates_set["observationTypeId"] = str(matches[0].id)

        if (has_observation_type or updates_set) and (typology is not None or method is not None):
            if typology is not None:
                updates_unset["typology"] = ""
            if method is not None:
                updates_unset["method"] = ""

        if not updates_set and not updates_unset:
            skipped += 1
            continue

        if not dry_run:
            update = {}
            if updates_set:
                update["$set"] = updates_set
            if updates_unset:
                update["$unset"] = updates_unset
            detection_collection.update_one({"_id": det["_id"]}, update)
        updated += 1

    print(
        f"DetectionType migration: updated={updated}, skipped={skipped}, "
        f"ambiguous_or_missing={ambiguous}"
    )
    return 0 if ambiguous == 0 else 1


def migrate_observation_types(default_category: str | None, dry_run: bool):
    texts = load_detection_texts()
    if not texts:
        print("No legacy detection_text collection found, skipping observation type backfill.")
        return

    obs_by_key = build_observation_map()
    updated = 0
    skipped = 0

    for text in texts:
        key = (text.get("typology"), text.get("method"))
        matches = obs_by_key.get(key, [])
        if len(matches) != 1:
            skipped += 1
            continue
        obs = matches[0]

        updates = {}
        if not obs.category:
            if default_category is None:
                skipped += 1
                continue
            updates["category"] = default_category
        if not obs.locationAndScoreInstructions:
            updates["locationAndScoreInstructions"] = text.get("locationAndScoreInstructions", "")
        if not obs.bchInstructions:
            updates["bchInstructions"] = text.get("bbchInstructions", "")

        if updates:
            for key_name, value in updates.items():
                setattr(obs, key_name, value)
            if not dry_run:
                obs.save()
            updated += 1
        else:
            skipped += 1

    print(f"ObservationType backfill: updated={updated}, skipped={skipped}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate detection types to observationTypeId and backfill observation types."
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes.")
    parser.add_argument(
        "--default-category",
        default=None,
        help="Default category for observation types missing category.",
    )
    args = parser.parse_args()

    connect_db()

    exit_code = migrate_detection_types(dry_run=args.dry_run)
    migrate_observation_types(default_category=args.default_category, dry_run=args.dry_run)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
