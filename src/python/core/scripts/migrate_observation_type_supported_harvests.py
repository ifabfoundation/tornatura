#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections import defaultdict

from mongoengine import connect

from core.config import APIConfig
from core.models import HarvestType, ObservationType


INITIAL_MAPPING = {
    "vite": [
        {"typology": "Giallumi", "method": "Foglia", "category": "Batterio"},
        {"typology": "Giallumi", "method": "Frutto", "category": "Batterio"},
        {"typology": "Giallumi", "method": "Tutta la pianta", "category": "Batterio"},
        {"typology": "Peronospora", "method": "Foglia", "category": "Fungo e peronospora"},
        {"typology": "Peronospora", "method": "Frutto", "category": "Fungo e peronospora"},
        {"typology": "Peronospora", "method": "Tutta la pianta", "category": "Fungo e peronospora"},
        {"typology": "Scafoideo", "method": "Pianta", "category": "Insetto"},
        {"typology": "Scafoideo", "method": "Trappola", "category": "Insetto"},
    ],
    "pero": [
        {"typology": "Cimice", "method": "Pianta", "category": "Insetto"},
        {"typology": "Cimice", "method": "Trappola", "category": "Insetto"},
    ],
    "pesco": [
        {"typology": "Cimice", "method": "Pianta", "category": "Insetto"},
        {"typology": "Cimice", "method": "Trappola", "category": "Insetto"},
    ],
    "mais": [
        {"typology": "Diabrotica", "method": "Pianta", "category": "Insetto"},
        {"typology": "Diabrotica", "method": "Trappola", "category": "Insetto"},
    ],
    "barbabietola": [
        {"typology": "Lisso", "method": "Pianta", "category": "Insetto"},
        {"typology": "Lisso", "method": "Trappola", "category": "Insetto"},
        {"typology": "Nottua  Autographa gamma", "method": "Pianta", "category": "Insetto"},
        {"typology": "Nottua  Autographa gamma", "method": "Trappola", "category": "Insetto"},
        {"typology": "Nottua  Mamestra brassicae", "method": "Pianta", "category": "Insetto"},
        {"typology": "Nottua  Mamestra brassicae", "method": "Trappola", "category": "Insetto"},
        {"typology": "Nottua  Spodoptera exigua", "method": "Pianta", "category": "Insetto"},
        {"typology": "Nottua  Spodoptera exigua", "method": "Trappola", "category": "Insetto"},
        {"typology": "Cleono", "method": "Pianta", "category": "Insetto"},
        {"typology": "Cleono", "method": "Trappola", "category": "Insetto"},
    ],
}

INACTIVE_LEGACY_HARVEST_TYPES = [
    {"code": "1", "label": "1"},
    {"code": "Albicocche", "label": "Albicocche"},
    {"code": "Avvocado", "label": "Avvocado"},
    {"code": "Banane", "label": "Banane"},
    {"code": "Cervelli", "label": "Cervelli"},
    {"code": "Grano", "label": "Grano"},
    {"code": "Mais", "label": "Mais (legacy)"},
    {"code": "Mele antiche", "label": "Mele antiche"},
    {"code": "Patata", "label": "Patata"},
    {"code": "Patata ", "label": "Patata (legacy trailing space)"},
    {"code": "Pere", "label": "Pere"},
    {"code": "Test", "label": "Test"},
    {"code": "Uliveto", "label": "Uliveto"},
    {"code": "Ulivi", "label": "Ulivi"},
    {"code": "Vite chardonnay", "label": "Vite chardonnay"},
    {"code": "d", "label": "d"},
    {"code": "ss", "label": "ss"},
]


def connect_db() -> None:
    connect(
        host=APIConfig.MONGO_DATABASE_HOST,
        db=APIConfig.MONGO_DATABASE_NAME,
        port=27017,
        username=APIConfig.MONGO_USER,
        password=APIConfig.MONGO_PASSWORD,
    )


def matcher_key(matcher: dict) -> tuple[str, str, str]:
    return (
        matcher["typology"],
        matcher["method"],
        matcher["category"],
    )


def build_observation_index() -> dict[tuple[str, str, str], list[ObservationType]]:
    index: dict[tuple[str, str, str], list[ObservationType]] = defaultdict(list)
    for observation_type in ObservationType.objects():
        key = (
            observation_type.typology,
            observation_type.method,
            observation_type.category,
        )
        index[key].append(observation_type)
    return index


def ensure_seed_harvest_types(seed_missing_inactive_harvest_types: bool, dry_run: bool) -> tuple[list[str], int]:
    missing_codes: list[str] = []
    created = 0

    required_codes = set(INITIAL_MAPPING.keys())
    existing_codes = {item.code for item in HarvestType.objects(code__in=list(required_codes))}
    for code in sorted(required_codes):
        if code not in existing_codes:
            missing_codes.append(code)

    if seed_missing_inactive_harvest_types:
        for payload in INACTIVE_LEGACY_HARVEST_TYPES:
            if HarvestType.objects(code=payload["code"]).first():
                continue
            if not dry_run:
                HarvestType(
                    code=payload["code"],
                    label=payload["label"],
                    active=False,
                    sortOrder=2000,
                    creationTime=0,
                    lastUpdateTime=0,
                ).save()
            created += 1

    return missing_codes, created


def migrate_supported_harvests(
    dry_run: bool,
    fail_on_missing: bool,
    fail_on_ambiguous: bool,
    seed_missing_inactive_harvest_types: bool,
) -> int:
    missing_harvest_types, created_inactive = ensure_seed_harvest_types(
        seed_missing_inactive_harvest_types=seed_missing_inactive_harvest_types,
        dry_run=dry_run,
    )
    if missing_harvest_types:
        print(f"Missing active HarvestType codes required by mapping: {missing_harvest_types}")
        return 1

    index = build_observation_index()
    counts = {
        "matched": 0,
        "updated": 0,
        "unchanged": 0,
        "missing": 0,
        "ambiguous": 0,
    }
    blocked: list[str] = []

    for harvest_code, matchers in INITIAL_MAPPING.items():
        for matcher in matchers:
            key = matcher_key(matcher)
            matches = index.get(key, [])

            if not matches:
                counts["missing"] += 1
                blocked.append(f"MISSING\t{harvest_code}\t{key}")
                continue

            if len(matches) > 1:
                counts["ambiguous"] += 1
                blocked.append(f"AMBIGUOUS\t{harvest_code}\t{key}\tcount={len(matches)}")
                continue

            observation_type = matches[0]
            counts["matched"] += 1
            current_codes = list(observation_type.supportedHarvestCodes or [])
            target_codes = sorted(set(current_codes + [harvest_code]))
            if target_codes == current_codes:
                counts["unchanged"] += 1
                continue

            if not dry_run:
                observation_type.supportedHarvestCodes = target_codes
                observation_type.save()
            counts["updated"] += 1

    print(
        "Observation type supported harvest migration summary: "
        f"matched={counts['matched']}, updated={counts['updated']}, "
        f"unchanged={counts['unchanged']}, missing={counts['missing']}, "
        f"ambiguous={counts['ambiguous']}, created_inactive={created_inactive}, dry_run={dry_run}"
    )
    if blocked:
        print("Blocked entries:")
        for item in blocked:
            print(f"- {item}")

    if counts["ambiguous"] > 0 and fail_on_ambiguous:
        return 1
    if counts["missing"] > 0 and fail_on_missing:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill ObservationType.supportedHarvestCodes from the approved initial mapping."
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes.")
    parser.add_argument("--apply", action="store_true", help="Write changes.")
    parser.add_argument("--fail-on-missing", action="store_true", help="Exit non-zero when a matcher has no matching observation type.")
    parser.add_argument("--fail-on-ambiguous", action="store_true", help="Exit non-zero when a matcher matches multiple observation types.")
    parser.add_argument(
        "--seed-missing-inactive-harvest-types",
        action="store_true",
        help="Also seed missing inactive legacy HarvestType records.",
    )
    args = parser.parse_args()

    if args.dry_run == args.apply:
        print("Choose exactly one of --dry-run or --apply.", file=sys.stderr)
        return 2

    connect_db()
    return migrate_supported_harvests(
        dry_run=args.dry_run,
        fail_on_missing=args.fail_on_missing,
        fail_on_ambiguous=args.fail_on_ambiguous,
        seed_missing_inactive_harvest_types=args.seed_missing_inactive_harvest_types,
    )


if __name__ == "__main__":
    sys.exit(main())
