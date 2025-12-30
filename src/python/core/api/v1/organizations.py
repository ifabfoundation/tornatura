from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from core.permissions import CanManageOrganization, CanViewOrganization, CanViewOrganizationMembers, IsAdmin, IsAgronomist, IsAuthenticated
from core.security import SecurityChecker
from core.serializers import AccountTypeEnum, ErrorResponse, Organization, OrganizationCreatePayload, OrganizationUpdatePayload, PaginatedResponse, OrganizationMember

from core.services.organizations_services import OrganizationCustomRole, OrganizationDefaultRole, OrganizationServices
from core.services.users_services import UserServices
from core.utils import paginate


router = APIRouter()


@router.get(
    "",
    operation_id="list_organization",
    summary="List organizations",
    response_description="List of organizations",
)
async def list_organizations(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    page: int = Query(1, ge=1, description="Page number"), 
    limit: int= Query(25, ge=25, le=1000, description="Items per page"),
    ) -> PaginatedResponse:

    organization_services = OrganizationServices()
    data = organization_services.list()
    total_count = len(data)
    data = paginate(data, page, limit)
    return PaginatedResponse(data=data, total=total_count, page=page, limit=limit)


@router.post(
    "",
    operation_id="create_organization",
    summary="Create Organization",
    response_description="Organization Info",
)
async def create_organization(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin, mutually_exclusive=True))],
    payload: OrganizationCreatePayload, 
    ) -> Organization:
    organization_services = OrganizationServices()
    # check if organization with the same name already exists
    if organization_services.is_organization_exists(payload.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Organization with the same name already exists"
        )
    
    organization = organization_services.create(payload)
    return organization


@router.get(
    "/{org_id}",
    operation_id="get_organization",
    summary="Current Organization Info",
    response_description="Organization Info",
)
async def get_organization(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    org_id: str = Path(..., description="Organization ID"), 
    ) -> Organization:
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)
   
    # Check object-level permissions
    checker = SecurityChecker(CanViewOrganization)
    checker.check_object_permission(token_info, organization)
    
    return organization


@router.put(
    "/{org_id}",
    operation_id="update_organization",
    summary="Update Organization Info",
    response_description="Organization Info",
)
async def update_organization(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    payload: OrganizationUpdatePayload, 
    org_id: str = Path(..., description="Organization ID"), 
    ) -> Organization:
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    # Check object-level permissions
    checker = SecurityChecker(CanManageOrganization)
    checker.check_object_permission(token_info, organization)
    
    organization = organization_services.update(org_id, payload)
    return organization


@router.get(
    "/{org_id}/members",
    operation_id="list_organization_members",
    summary="List Organization Members",
    response_description="Organization members with roles",
)
async def list_organization_members(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    org_id: str = Path(..., description="Organization ID"),
    ) -> List[OrganizationMember]:
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    checker = SecurityChecker(CanViewOrganizationMembers)
    checker.check_object_permission(token_info, organization)

    return organization_services.list_members(org_id)
