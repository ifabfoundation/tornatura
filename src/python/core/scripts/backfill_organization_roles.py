#!/usr/bin/env python3
"""
Backfill missing custom Keycloak roles for existing organizations.

The script iterates MongoDB organizations and attempts to create the expected
custom roles in Keycloak. Existing roles are treated as already synced.
"""
from __future__ import annotations

import argparse
import sys

from mongoengine import connect

import phasetwo
from phasetwo.apis.tags import organization_roles_api
from phasetwo.model.organization_role_representation import OrganizationRoleRepresentation

from core.config import APIConfig
from core.models import OrganizationModel
from core.services.organizations_services import (
    OrganizationCustomRole,
    get_service_access_token,
)


def connect_db() -> None:
    connect(
        host=APIConfig.MONGO_DATABASE_HOST,
        db=APIConfig.MONGO_DATABASE_NAME,
        port=27017,
        username=APIConfig.MONGO_USER,
        password=APIConfig.MONGO_PASSWORD,
    )


def get_roles_api() -> organization_roles_api.OrganizationRolesApi:
    configuration = phasetwo.Configuration(
        host=f"{APIConfig.KEYCLOAK_ENDPOINT}/realms",
        access_token=get_service_access_token(),
    )
    client = phasetwo.ApiClient(configuration)
    return organization_roles_api.OrganizationRolesApi(client)


def is_role_already_present(exc: phasetwo.ApiException) -> bool:
    if getattr(exc, "status", None) == 409:
        return True

    body = getattr(exc, "body", "") or ""
    return "already exists" in str(body).lower()


def backfill_roles(
    dry_run: bool,
    org_id: str | None,
    limit: int,
    include_deleted: bool,
) -> int:
    query = {}
    if not include_deleted:
        query["deleted"] = False
    if org_id:
        query["orgId"] = org_id

    organizations = OrganizationModel.objects(**query)
    if limit and limit > 0:
        organizations = organizations.limit(limit)

    roles_api = None if dry_run else get_roles_api()

    created = 0
    existing = 0
    missing_orgs = 0
    failed = 0
    processed_orgs = 0

    for organization in organizations:
        processed_orgs += 1
        print(f"Processing organization {organization.orgId} ({organization.name})")

        for role_name in OrganizationCustomRole:
            if dry_run:
                print(f"[dry-run] create role {role_name.value} in org {organization.orgId}")
                continue

            role = OrganizationRoleRepresentation(name=role_name.value)
            try:
                roles_api.create_organization_role(
                    role,
                    path_params={
                        "realm": APIConfig.KEYCLOAK_REALM,
                        "orgId": organization.orgId,
                    },
                )
                created += 1
                print(f"  created role: {role_name.value}")
            except phasetwo.ApiException as exc:
                if is_role_already_present(exc):
                    existing += 1
                    print(f"  role already present: {role_name.value}")
                    continue

                if getattr(exc, "status", None) == 404:
                    missing_orgs += 1
                    print(f"  organization missing in Keycloak: {organization.orgId}")
                    break

                failed += 1
                print(
                    f"  failed to create role {role_name.value}: "
                    f"status={getattr(exc, 'status', 'unknown')}"
                )

    print(
        "Role backfill summary: "
        f"organizations={processed_orgs}, created={created}, "
        f"already_present={existing}, missing_orgs={missing_orgs}, failed={failed}"
    )
    return 1 if failed > 0 else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create missing custom Keycloak organization roles for Mongo organizations."
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing changes.")
    parser.add_argument("--org-id", help="Only process a single organization orgId.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of organizations processed.")
    parser.add_argument(
        "--include-deleted",
        action="store_true",
        help="Also process Mongo organizations already marked as deleted.",
    )
    args = parser.parse_args()

    connect_db()
    return backfill_roles(
        dry_run=args.dry_run,
        org_id=args.org_id,
        limit=args.limit,
        include_deleted=args.include_deleted,
    )


if __name__ == "__main__":
    sys.exit(main())
