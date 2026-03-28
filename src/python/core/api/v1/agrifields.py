from typing import Annotated, List
from fastapi import APIRouter, Depends, Path, Query
from core.permissions import CanManageOrganizationAgrifields, CanViewOrganizationAgrifields, IsAuthenticated
from core.security import SecurityChecker
from core.serializers import AgriField, AgriFieldMutationPayload, ErrorResponse, PaginatedResponse, StatusResponse
from core.services.agrifields_services import AgriFieldServices
from core.services.organizations_services import OrganizationServices
from core.utils import paginate


router = APIRouter()


@router.get(
    "",
    tags=["AgriFields"],
    operation_id="list_agrifields",
    summary="List Agriculture Fields",
    response_description="List of Agriculture Fields",
    dependencies=[Depends(SecurityChecker(IsAuthenticated))]
)
async def list_agrifields(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    org_id: str = Path(..., description="Organization ID"), 
    page: int = Query(1, ge=1, description="Page number"), 
    limit: int= Query(25, ge=25, le=1000, description="Items per page")
    ) -> PaginatedResponse:
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    # Check object-level permissions
    checker = SecurityChecker(CanViewOrganizationAgrifields)
    checker.check_object_permission(token_info, organization)

    agrifield_service = AgriFieldServices()
    data = agrifield_service.list(org_id)
    total_count = len(data)
    data = paginate(data, page, limit)
    return PaginatedResponse(data=data, total=total_count, page=page, limit=limit)


@router.post(
    "",
    tags=["AgriFields"],
    operation_id="create_agrifield",
    summary="Create Agriculture Field",
    response_description="Agriculture Field detail",
)
async def create_agrifield(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    payload: AgriFieldMutationPayload,
    org_id: str = Path(..., description="Organization ID")
    ) -> AgriField:

    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    # Check object-level permissions
    checker = SecurityChecker(CanManageOrganizationAgrifields)
    checker.check_object_permission(token_info, organization)

    agrifield_service = AgriFieldServices()
    agrifield = agrifield_service.create(org_id, payload, token_info["sub"])


    return agrifield   


@router.get(
    "/{agrifield_id}",
    tags=["AgriFields"],
    operation_id="get_agrifield",
    summary="Get Agriculture Field details",
    response_description="Agriculture Field detail",
)
async def get_agrifield(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    org_id: str = Path(..., description="Organization ID"),
    agrifield_id: str = Path(..., description="Agrifield ID")
    ) -> AgriField:

    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    # Check object-level permissions
    checker = SecurityChecker(CanManageOrganizationAgrifields)
    checker.check_object_permission(token_info, organization)

    agrifield_service = AgriFieldServices()
    agrifield = agrifield_service.get(agrifield_id)

    return agrifield


@router.delete(
    "/{agrifield_id}",
    tags=["AgriFields"],
    operation_id="delete_agrifield",
    summary="Detetion of Agriculture Field",
    response_description="Deletion status",
)
async def delete_agrifield(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    org_id: str = Path(..., description="Organization ID"),
    agrifield_id: str = Path(..., description="Agrifield ID")
    ) -> StatusResponse:

    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    # Check object-level permissions
    checker = SecurityChecker(CanManageOrganizationAgrifields)
    checker.check_object_permission(token_info, organization)

    agrifield_service = AgriFieldServices()
    agrifield_service.delete(agrifield_id)

    response = {"status": 200, "message": "Agrifield deleted successfully"}
    response = StatusResponse(**response)

    return response

@router.put(
    "/{agrifield_id}",
    tags=["AgriFields"],
    operation_id="update_agrifield",
    summary="Update of Agriculture Field",
    response_description="Updated Agriculture Field detail",
)
async def update_agrifield(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    payload: AgriFieldMutationPayload,
    org_id: str = Path(..., description="Organization ID"),
    agrifield_id: str = Path(..., description="Agrifield ID"),
    ) -> AgriField:

    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    # Check object-level permissions
    checker = SecurityChecker(CanManageOrganizationAgrifields)
    checker.check_object_permission(token_info, organization)

    agrifield_service = AgriFieldServices()
    agrifield = agrifield_service.update(agrifield_id, payload)

    return agrifield
