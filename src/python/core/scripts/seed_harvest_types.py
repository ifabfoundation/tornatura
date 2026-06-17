#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from mongoengine import connect

from core.config import APIConfig
from core.models import HarvestType


ACTIVE_HARVEST_TYPES = [
    {"code": "vite", "label": "Vite", "active": True, "sortOrder": 10},
    {"code": "pero", "label": "Pero", "active": True, "sortOrder": 20},
    {"code": "pesco", "label": "Pesco", "active": True, "sortOrder": 30},
    {"code": "mais", "label": "Mais", "active": True, "sortOrder": 40},
    {"code": "barbabietola", "label": "Barbabietola", "active": True, "sortOrder": 50},
    {"code": "olivo", "label": "Olivo", "active": True, "sortOrder": 60},
    {"code": "agrumi", "label": "Agrumi", "active": True, "sortOrder": 70},
    {"code": "albicocco", "label": "Albicocco", "active": True, "sortOrder": 80},
]


INACTIVE_LEGACY_HARVEST_TYPES = [
    {"code": "1", "label": "1", "active": False, "sortOrder": 1000},
    {"code": "albicocca", "label": "Albicocca (legacy)", "active": False, "sortOrder": 1005},
    {"code": "Albicocche", "label": "Albicocche", "active": False, "sortOrder": 1010},
    {"code": "Avvocado", "label": "Avvocado", "active": False, "sortOrder": 1020},
    {"code": "Banane", "label": "Banane", "active": False, "sortOrder": 1030},
    {"code": "Cervelli", "label": "Cervelli", "active": False, "sortOrder": 1040},
    {"code": "Grano", "label": "Grano", "active": False, "sortOrder": 1050},
    {"code": "Mais", "label": "Mais (legacy)", "active": False, "sortOrder": 1060},
    {"code": "Mele antiche", "label": "Mele antiche", "active": False, "sortOrder": 1070},
    {"code": "Patata", "label": "Patata", "active": False, "sortOrder": 1080},
    {"code": "Patata ", "label": "Patata (legacy trailing space)", "active": False, "sortOrder": 1090},
    {"code": "Pere", "label": "Pere", "active": False, "sortOrder": 1100},
    {"code": "Test", "label": "Test", "active": False, "sortOrder": 1110},
    {"code": "Uliveto", "label": "Uliveto", "active": False, "sortOrder": 1120},
    {"code": "Ulivi", "label": "Ulivi", "active": False, "sortOrder": 1130},
    {"code": "Vite chardonnay", "label": "Vite chardonnay", "active": False, "sortOrder": 1140},
    {"code": "d", "label": "d", "active": False, "sortOrder": 1150},
    {"code": "ss", "label": "ss", "active": False, "sortOrder": 1160},
]


def connect_db() -> None:
    connect(
        host=APIConfig.MONGO_DATABASE_HOST,
        db=APIConfig.MONGO_DATABASE_NAME,
        port=27017,
        username=APIConfig.MONGO_USER,
        password=APIConfig.MONGO_PASSWORD,
    )


def upsert_harvest_type(payload: dict, dry_run: bool) -> str:
    existing = HarvestType.objects(code=payload["code"]).first()
    if not existing:
        if not dry_run:
            HarvestType(
                code=payload["code"],
                label=payload["label"],
                active=payload["active"],
                sortOrder=payload["sortOrder"],
                creationTime=0,
                lastUpdateTime=0,
            ).save()
        return "created"

    changed = False
    for field in ("label", "active", "sortOrder"):
        if getattr(existing, field) != payload[field]:
            changed = True
            if not dry_run:
                setattr(existing, field, payload[field])

    if changed:
        if not dry_run:
            existing.save()
        return "updated"

    return "unchanged"


def seed_harvest_types(include_inactive_legacy: bool, dry_run: bool) -> int:
    created = 0
    updated = 0
    unchanged = 0

    entries = list(ACTIVE_HARVEST_TYPES)
    if include_inactive_legacy:
        entries.extend(INACTIVE_LEGACY_HARVEST_TYPES)

    for payload in entries:
        result = upsert_harvest_type(payload, dry_run=dry_run)
        print(f"{result.upper()}: code={payload['code']!r} active={payload['active']} label={payload['label']!r}")
        if result == "created":
            created += 1
        elif result == "updated":
            updated += 1
        else:
            unchanged += 1

    print(
        "Harvest type seed summary: "
        f"created={created}, updated={updated}, unchanged={unchanged}, "
        f"include_inactive_legacy={include_inactive_legacy}, dry_run={dry_run}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed active and optional inactive legacy HarvestType records.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes.")
    parser.add_argument("--apply", action="store_true", help="Write changes in DB.")
    parser.add_argument(
        "--include-inactive-legacy",
        action="store_true",
        help="Also seed inactive legacy harvest codes discovered in Phase 0 audit.",
    )
    args = parser.parse_args()

    if args.dry_run == args.apply:
        print("Choose exactly one of --dry-run or --apply.", file=sys.stderr)
        return 2

    connect_db()
    return seed_harvest_types(
        include_inactive_legacy=args.include_inactive_legacy,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
