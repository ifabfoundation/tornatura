#!/usr/bin/env python3
"""
Unset unused top-level fields on Organization documents.

This script keeps only the fields defined in OrganizationModel and removes any
extra top-level keys found in MongoDB.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter

from mongoengine import connect

from core.config import APIConfig
from core.models import OrganizationModel


ALLOWED_FIELDS = {
    "orgId",
    "name",
    "piva",
    "logo",
    "cover",
    "contacts",
    "deleted",
    "creationTime",
    "lastUpdateTime",
}


def connect_db() -> None:
    connect(
        host=APIConfig.MONGO_DATABASE_HOST,
        port=27017,
        username=APIConfig.MONGO_USER,
        password=APIConfig.MONGO_PASSWORD,
    )


def cleanup_organizations(dry_run: bool, org_id: str | None, limit: int) -> int:
    db = OrganizationModel._get_db()
    collection = db[OrganizationModel._get_collection_name()]

    query = {}
    if org_id:
        query["orgId"] = org_id

    cursor = collection.find(query)
    if limit and limit > 0:
        cursor = cursor.limit(limit)

    updated = 0
    skipped = 0
    field_counts = Counter()

    for doc in cursor:
        extra_fields = set(doc.keys()) - ALLOWED_FIELDS - {"_id"}
        if not extra_fields:
            skipped += 1
            continue

        unset_payload = {field: "" for field in sorted(extra_fields)}
        for field in extra_fields:
            field_counts[field] += 1

        if not dry_run:
            collection.update_one({"_id": doc["_id"]}, {"$unset": unset_payload})

        updated += 1

    print(
        "Organization cleanup: "
        f"updated={updated}, skipped={skipped}, "
        f"fields_removed={sum(field_counts.values())}"
    )

    if field_counts:
        print("Removed fields by frequency:")
        for field, count in field_counts.most_common():
            print(f"- {field}: {count}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove unused top-level fields from Organization documents."
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes.")
    parser.add_argument("--org-id", help="Only process a single organization orgId.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of documents processed.")
    args = parser.parse_args()

    connect_db()
    return cleanup_organizations(dry_run=args.dry_run, org_id=args.org_id, limit=args.limit)


if __name__ == "__main__":
    sys.exit(main())
