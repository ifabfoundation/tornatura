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
import json
import sys

from mongoengine import connect

from core.config import APIConfig
from core.services.organization_stats_services import OrganizationStatsServices


def connect_db() -> None:
    connect(
        host=APIConfig.MONGO_DATABASE_HOST,
        db=APIConfig.MONGO_DATABASE_NAME,
        port=27017,
        username=APIConfig.MONGO_USER,
        password=APIConfig.MONGO_PASSWORD,
    )

def generate_organization_stats(org_id: str, months: int) -> dict:
    return OrganizationStatsServices().get_organization_stats(org_id=org_id, months=months)


def generate_all_organizations_stats(months: int) -> list[dict]:
    return OrganizationStatsServices().list_organization_stats(months=months)


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
