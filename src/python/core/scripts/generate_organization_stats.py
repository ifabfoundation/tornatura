#!/usr/bin/env python3
"""
Generate recent organization statistics.

The report includes:
- current agrifield count for the organization
- distinct harvest values across current agrifields
- per-agrifield detection counts within the requested time window
"""
from __future__ import annotations

import argparse
import calendar
import json
import sys
from datetime import datetime, timezone

from mongoengine import connect

from core.config import APIConfig
from core.models import AgriFieldModel, DetectionModel, OrganizationModel


def connect_db() -> None:
    connect(
        host=APIConfig.MONGO_DATABASE_HOST,
        db=APIConfig.MONGO_DATABASE_NAME,
        port=27017,
        username=APIConfig.MONGO_USER,
        password=APIConfig.MONGO_PASSWORD,
    )


def subtract_months(reference: datetime, months: int) -> datetime:
    month_index = reference.month - months
    year = reference.year + (month_index - 1) // 12
    month = (month_index - 1) % 12 + 1
    day = min(reference.day, calendar.monthrange(year, month)[1])
    return reference.replace(year=year, month=month, day=day)


def normalize_harvest(harvest: str | None) -> str | None:
    if harvest is None:
        return None
    harvest = harvest.strip()
    return harvest or None


def build_detection_counts(agrifield_ids: list[str], window_start_ms: int) -> dict[str, int]:
    if not agrifield_ids:
        return {}

    collection = DetectionModel._get_collection()
    pipeline = [
        {
            "$match": {
                "deleted": False,
                "agrifieldId": {"$in": agrifield_ids},
                "$expr": {
                    "$gte": [
                        {"$ifNull": ["$detectionTime", "$creationTime"]},
                        window_start_ms,
                    ]
                },
            }
        },
        {
            "$group": {
                "_id": "$agrifieldId",
                "count": {"$sum": 1},
            }
        },
    ]

    return {
        item["_id"]: item["count"]
        for item in collection.aggregate(pipeline)
    }


def generate_organization_stats(org_id: str, months: int) -> dict:
    organization = OrganizationModel.objects(orgId=org_id, deleted=False).first()
    if organization is None:
        raise ValueError(f"Organization not found or deleted: {org_id}")

    now = datetime.now(timezone.utc)
    window_start = subtract_months(now, months)
    window_start_ms = int(window_start.timestamp() * 1000)
    window_end_ms = int(now.timestamp() * 1000)

    agrifields = list(
        AgriFieldModel.objects(orgId=org_id, deleted=False).order_by("name", "creationTime")
    )
    agrifield_ids = [str(agrifield.id) for agrifield in agrifields]
    detection_counts = build_detection_counts(agrifield_ids, window_start_ms)

    distinct_harvests = sorted(
        {
            harvest
            for harvest in (normalize_harvest(agrifield.harvest) for agrifield in agrifields)
            if harvest is not None
        }
    )

    return {
        "organization": {
            "orgId": organization.orgId,
            "name": organization.name,
        },
        "window": {
            "months": months,
            "start": window_start.isoformat(),
            "end": now.isoformat(),
            "startTimestampMs": window_start_ms,
            "endTimestampMs": window_end_ms,
        },
        "agrifieldCount": len(agrifields),
        "distinctHarvestCount": len(distinct_harvests),
        "distinctHarvests": distinct_harvests,
        "agrifields": [
            {
                "id": str(agrifield.id),
                "name": agrifield.name,
                "harvest": normalize_harvest(agrifield.harvest),
                "year": agrifield.year,
                "detectionCount": detection_counts.get(str(agrifield.id), 0),
            }
            for agrifield in agrifields
        ],
    }


def generate_all_organizations_stats(months: int) -> list[dict]:
    organizations = OrganizationModel.objects(deleted=False).order_by("name", "creationTime")
    return [
        generate_organization_stats(org_id=organization.orgId, months=months)
        for organization in organizations
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate agrifield and detection stats for an organization."
    )
    parser.add_argument("--org-id", help="Organization orgId.")
    parser.add_argument(
        "--all-orgs",
        action="store_true",
        help="Generate stats for all non-deleted organizations and return a list.",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=3,
        help="Rolling time window in months used for detection counts. Default: 3.",
    )
    args = parser.parse_args()

    if args.months <= 0:
        print("--months must be greater than 0", file=sys.stderr)
        return 1

    if args.all_orgs and args.org_id:
        print("Use either --org-id or --all-orgs, not both", file=sys.stderr)
        return 1

    if not args.all_orgs and not args.org_id:
        print("Either --org-id or --all-orgs is required", file=sys.stderr)
        return 1

    connect_db()

    try:
        if args.all_orgs:
            stats = generate_all_organizations_stats(months=args.months)
        else:
            stats = generate_organization_stats(org_id=args.org_id, months=args.months)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(stats, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
