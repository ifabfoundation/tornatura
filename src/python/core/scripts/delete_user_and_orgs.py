#!/usr/bin/env python3
"""
Delete a Keycloak user and organizations related to that user.

Related organizations are resolved from the Phase Two memberships endpoint:
GET /realms/{realm}/users/{userId}/orgs
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib import error, request

from keycloak import KeycloakAdmin, KeycloakOpenID

from core import config


def get_keycloak_admin() -> KeycloakAdmin:
    return KeycloakAdmin(
        server_url=config.APIConfig.KEYCLOAK_ENDPOINT,
        client_id=config.APIConfig.KEYCLOAK_CLIENT_ID,
        client_secret_key=config.APIConfig.KEYCLOAK_CLIENT_SECRET,
        realm_name=config.APIConfig.KEYCLOAK_REALM,
    )


def get_service_access_token() -> str:
    keycloak_openid = KeycloakOpenID(
        server_url=config.APIConfig.KEYCLOAK_ENDPOINT,
        client_id=config.APIConfig.KEYCLOAK_CLIENT_ID,
        client_secret_key=config.APIConfig.KEYCLOAK_CLIENT_SECRET,
        realm_name=config.APIConfig.KEYCLOAK_REALM,
    )
    auth_payload = keycloak_openid.token(grant_type=["client_credentials"])
    return auth_payload["access_token"]


def _realm_url(path: str) -> str:
    endpoint = config.APIConfig.KEYCLOAK_ENDPOINT.rstrip("/")
    realm = config.APIConfig.KEYCLOAK_REALM
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


def _request_delete(path: str, token: str, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] DELETE {_realm_url(path)}")
        return

    req = request.Request(
        url=_realm_url(path),
        method="DELETE",
        headers={"Authorization": f"Bearer {token}"},
    )
    with request.urlopen(req):
        return


def resolve_user_id(admin: KeycloakAdmin, user_id: str | None, email: str | None) -> str:
    if user_id:
        admin.get_user(user_id)
        return user_id

    assert email is not None
    resolved = admin.get_user_id(email)
    if not resolved:
        raise ValueError(f"User not found for email: {email}")
    return resolved


def list_user_org_ids(token: str, user_id: str) -> list[str]:
    data = _request_json("GET", f"/users/{user_id}/orgs", token)
    if not isinstance(data, list):
        return []

    org_ids = []
    for org in data:
        if isinstance(org, dict) and org.get("id"):
            org_ids.append(org["id"])
    return org_ids


def delete_user_and_organizations(user_id: str, dry_run: bool) -> int:
    token = get_service_access_token()
    admin = get_keycloak_admin()

    org_ids = list_user_org_ids(token, user_id)
    print(f"Found {len(org_ids)} related organization(s) for user {user_id}.")

    org_delete_errors = 0
    for org_id in org_ids:
        try:
            _request_delete(f"/orgs/{org_id}", token, dry_run=dry_run)
            print(f"Deleted organization: {org_id}")
        except error.HTTPError as exc:
            org_delete_errors += 1
            print(
                f"Failed to delete organization {org_id}: "
                f"HTTP {exc.code} {exc.reason}"
            )

    if org_delete_errors > 0:
        print("User deletion skipped because one or more organizations could not be deleted.")
        return 1

    if dry_run:
        print(f"[dry-run] delete user {user_id}")
        return 0

    admin.delete_user(user_id)
    print(f"Deleted user: {user_id}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Delete a Keycloak user and their related organizations."
    )
    parser.add_argument("--user-id", help="Keycloak user ID to delete.")
    parser.add_argument("--email", help="User email (username) to resolve Keycloak user ID.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without deleting.")
    args = parser.parse_args()

    if not args.user_id and not args.email:
        print("Provide one of --user-id or --email.")
        return 2

    if args.user_id and args.email:
        print("Use only one identifier: --user-id or --email.")
        return 2

    try:
        admin = get_keycloak_admin()
        user_id = resolve_user_id(admin, args.user_id, args.email)
        return delete_user_and_organizations(user_id, dry_run=args.dry_run)
    except error.HTTPError as exc:
        print(f"Request failed: HTTP {exc.code} {exc.reason}")
        return 1
    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
