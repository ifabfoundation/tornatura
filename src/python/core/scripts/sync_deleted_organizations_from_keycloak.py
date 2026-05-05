#!/usr/bin/env python3
"""
Mark MongoDB organizations as deleted when their Keycloak organization is missing.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from urllib import error, request

from mongoengine import connect

from core.config import APIConfig
from core.models import OrganizationModel
from core.services.organizations_services import get_service_access_token


def connect_db() -> None:
    connect(
        host=APIConfig.MONGO_DATABASE_HOST,
        db=APIConfig.MONGO_DATABASE_NAME,
        port=27017,
        username=APIConfig.MONGO_USER,
        password=APIConfig.MONGO_PASSWORD,
    )


def _realm_url(path: str) -> str:
    endpoint = APIConfig.KEYCLOAK_ENDPOINT.rstrip("/")
    realm = APIConfig.KEYCLOAK_REALM
    return f"{endpoint}/realms/{realm}{path}"


def _request_json(method: str, path: str, token: str) -> object:
    req = request.Request(
        url=_realm_url(path),
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )
    with request.urlopen(req) as response:
        body = response.read().decode("utf-8")
        if not body:
            return {}
        return json.loads(body)


def keycloak_org_exists(token: str, org_id: str) -> bool:
    try:
        _request_json("GET", f"/orgs/{org_id}", token)
        return True
    except error.HTTPError as exc:
        if exc.code == 404:
            return False
        raise


def sync_deleted_organizations(dry_run: bool, org_id: str | None, limit: int) -> int:
    token = get_service_access_token()

    query = {"deleted": False}
    if org_id:
        query["orgId"] = org_id

    organizations = OrganizationModel.objects(**query)
    if limit and limit > 0:
        organizations = organizations.limit(limit)

    checked = 0
    marked_deleted = 0
    already_present = 0
    failed = 0

    for organization in organizations:
        checked += 1
        try:
            if keycloak_org_exists(token, organization.orgId):
                already_present += 1
                print(f"Organization present in Keycloak: {organization.orgId}")
                continue

            print(f"Organization missing in Keycloak: {organization.orgId}")
            if dry_run:
                print(f"[dry-run] mark Mongo organization as deleted: {organization.orgId}")
                marked_deleted += 1
                continue

            organization.deleted = True
            organization.lastUpdateTime = int(
                datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000
            )
            organization.save()
            marked_deleted += 1
        except error.HTTPError as exc:
            failed += 1
            print(
                f"Failed to check organization {organization.orgId}: "
                f"HTTP {exc.code} {exc.reason}"
            )
        except Exception as exc:
            failed += 1
            print(f"Failed to sync organization {organization.orgId}: {exc}")

    print(
        "Organization sync summary: "
        f"checked={checked}, present={already_present}, "
        f"marked_deleted={marked_deleted}, failed={failed}"
    )
    return 1 if failed > 0 else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mark Mongo organizations as deleted when the Keycloak organization is missing."
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing changes.")
    parser.add_argument("--org-id", help="Only process a single organization orgId.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of organizations processed.")
    args = parser.parse_args()

    connect_db()
    return sync_deleted_organizations(
        dry_run=args.dry_run,
        org_id=args.org_id,
        limit=args.limit,
    )


if __name__ == "__main__":
    sys.exit(main())
