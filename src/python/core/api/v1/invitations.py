from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query

from core.permissions import CanManageInvitations, IsAuthenticated, CanManageOrganizationInvitations
from core.security import SecurityChecker
from core.serializers import (
    Invitation,
    InvitationCreatePayload,
    InvitationAcceptPayload,
    InvitationValidateResponse,
    StatusResponse
)
from core.services.invitations_services import InvitationServices
from core.services.organizations_services import OrganizationServices


router = APIRouter()


@router.post(
    "/invitations",
    operation_id="create_invitation",
    summary="Create Invitation",
    response_description="Invitation created",
)
async def create_invitation(
    payload: InvitationCreatePayload,
    token_info: Annotated[dict, Depends(SecurityChecker(CanManageInvitations))]
) -> Invitation:
    """
    Create a new invitation

    Two scenarios:
    1. Standard invitation: orgId provided in payload, invitee joins that org
    2. Agronomist → New Company Owner: orgId is null in payload, company owner creates org later

    Permissions:
    - Company Owner can invite managers/standard/agronomists
    - Agronomist can invite company owners
    - Company Manager can invite standard users
    """
    invitation_services = InvitationServices()

    if payload.orgId:
        organization_services = OrganizationServices()
        organization = organization_services.get(payload.orgId)

        # Check object-level permissions
        checker = SecurityChecker(CanManageOrganizationInvitations)
        checker.check_object_permission(token_info, organization)

    return invitation_services.create(payload.orgId, payload, token_info)


@router.get(
    "/invitations/validate",
    operation_id="validate_invitation_token",
    summary="Validate Invitation Token",
    response_description="Invitation validation result",
)
async def validate_invitation_token(
    token: str = Query(..., description="Invitation token")
) -> InvitationValidateResponse:
    """
    Validate an invitation token (public endpoint, no auth required)
    Returns invitation details if valid
    """
    invitation_services = InvitationServices()
    return invitation_services.validate_token(token)


@router.post(
    "/invitations/accept",
    operation_id="accept_invitation",
    summary="Accept Invitation",
    response_description="Invitation accepted",
)
async def accept_invitation(
    payload: InvitationAcceptPayload,
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))]
) -> StatusResponse:
    """
    Accept an invitation (user must be authenticated)
    Adds user to organization and assigns role

    Special case: When a company owner accepts an invitation from an agronomist,
    they may need to provide orgId if they already have an organization.
    If they don't have an organization yet, they need to create one first.
    """
    invitation_services = InvitationServices()
    user_id = token_info["sub"]
    return invitation_services.accept(payload.token, user_id, token_info, payload.orgId)


@router.post(
    "/invitations/decline",
    operation_id="decline_invitation",
    summary="Decline Invitation",
    response_description="Invitation declined",
)
async def decline_invitation(
    payload: InvitationAcceptPayload
) -> StatusResponse:
    """
    Decline an invitation (no auth required - uses token)
    """
    invitation_services = InvitationServices()
    return invitation_services.decline(payload.token)

@router.get(
    "/invitations/byOrg",
    operation_id="list_organization_invitations",
    summary="List Organization Invitations",
    response_description="List of invitations",
)
async def list_organization_invitations(
    org_id: str = Query(..., description="Organization ID"),
    token_info: Annotated[dict, Depends(SecurityChecker(CanManageInvitations))] = None,
    status: Optional[str] = Query("pending", description="Filter by status")
) -> List[Invitation]:
    """
    List all invitations for an organization
    Filter by status: pending, accepted, declined, expired
    """
    invitation_services = InvitationServices()
   
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    # Check object-level permissions
    checker = SecurityChecker(CanManageOrganizationInvitations)
    checker.check_object_permission(token_info, organization)

    return invitation_services.list_by_organization(org_id, status)


@router.get(
    "/invitations/me",
    operation_id="list_my_invitations",
    summary="List My Invitations",
    response_description="List of pending invitations",
)
async def list_my_invitations(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))]
) -> List[Invitation]:
    """
    List all pending invitations for the authenticated user
    Matches by email from Keycloak profile
    """
    invitation_services = InvitationServices()
    user_email = token_info.get("email", "")
    return invitation_services.list_by_email(user_email)


@router.delete(
    "/invitations/{invitation_id}",
    operation_id="revoke_invitation",
    summary="Revoke Invitation",
    response_description="Invitation revoked",
)
async def revoke_invitation(
    invitation_id: str,
    token_info: Annotated[dict, Depends(SecurityChecker(CanManageInvitations))]
) -> StatusResponse:
    """
    Revoke (soft delete) a pending invitation
    """
    invitation_services = InvitationServices()
    invitation = invitation_services.get(invitation_id=invitation_id, token_info=token_info)

    if invitation.orgId:
        organization_services = OrganizationServices()
        organization = organization_services.get(invitation.orgId)

        # Check object-level permissions
        checker = SecurityChecker(CanManageOrganizationInvitations)
        checker.check_object_permission(token_info, organization)

    return invitation_services.delete(invitation_id)


@router.post(
    "/invitations/{invitation_id}/resend",
    operation_id="resend_invitation",
    summary="Resend Invitation",
    response_description="Invitation resent",
)
async def resend_invitation(
    invitation_id: str,
    token_info: Annotated[dict, Depends(SecurityChecker(CanManageInvitations))]
) -> StatusResponse:
    """
    Resend invitation email (generates new token)
    """
    invitation_services = InvitationServices()
    invitation = invitation_services.get(invitation_id=invitation_id, token_info=token_info)

    if invitation.orgId:
        organization_services = OrganizationServices()
        organization = organization_services.get(invitation.orgId)

        # Check object-level permissions
        checker = SecurityChecker(CanManageOrganizationInvitations)
        checker.check_object_permission(token_info, organization)

    return invitation_services.resend(invitation_id)
