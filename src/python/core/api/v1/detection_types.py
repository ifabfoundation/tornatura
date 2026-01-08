from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status

from core.permissions import CanManageOrganizationAgrifields, CanViewOrganizationAgrifields, IsAuthenticated
from core.security import SecurityChecker
from core.serializers import (
    DetectionType,
    DetectionTypeCreatePayload,
    DetectionTypeUpdatePayload,
    PaginatedResponse,
    StatusResponse,
)
from core.services.agrifields_services import AgriFieldServices
from core.services.detection_types_services import DetectionTypeServices
from core.services.organizations_services import OrganizationServices
from core.utils import paginate


router = APIRouter()


@router.get(
    "",
    operation_id="list_detection_types",
    summary="List Detection Types",
    response_description="List of detection types",
)
async def list_detection_types(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    org_id: str = Path(..., description="Organization ID"),
    agrifield_id: str = Path(..., description="Agriculture Field ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=1000, description="Items per page"),
) -> PaginatedResponse:
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    checker = SecurityChecker(CanViewOrganizationAgrifields)
    checker.check_object_permission(token_info, organization)

    agrifield_service = AgriFieldServices()
    agrifield_service.get(agrifield_id)

    detection_type_services = DetectionTypeServices()
    data = detection_type_services.list(agrifield_id)
    total_count = len(data)
    data = paginate(data, page, limit)
    return PaginatedResponse(data=data, total=total_count, page=page, limit=limit)


@router.post(
    "",
    operation_id="create_detection_type",
    summary="Create Detection Type",
    response_description="Detection type detail",
)
async def create_detection_type(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    payload: DetectionTypeCreatePayload,
    org_id: str = Path(..., description="Organization ID"),
    agrifield_id: str = Path(..., description="Agriculture Field ID"),
) -> DetectionType:
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    checker = SecurityChecker(CanManageOrganizationAgrifields)
    checker.check_object_permission(token_info, organization)

    agrifield_service = AgriFieldServices()
    agrifield_service.get(agrifield_id)

    detection_type_services = DetectionTypeServices()
    detection_type = detection_type_services.create(agrifield_id, payload)
    return detection_type


@router.get(
    "/{detection_type_id}",
    operation_id="get_detection_type",
    summary="Get Detection Type",
    response_description="Detection type detail",
)
async def get_detection_type(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    org_id: str = Path(..., description="Organization ID"),
    agrifield_id: str = Path(..., description="Agriculture Field ID"),
    detection_type_id: str = Path(..., description="Detection Type ID"),
) -> DetectionType:
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    checker = SecurityChecker(CanViewOrganizationAgrifields)
    checker.check_object_permission(token_info, organization)

    agrifield_service = AgriFieldServices()
    agrifield_service.get(agrifield_id)

    detection_type_services = DetectionTypeServices()
    detection_type = detection_type_services.get(detection_type_id)
    if detection_type.agrifieldId != agrifield_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection type not found"
        )
    return detection_type


@router.put(
    "/{detection_type_id}",
    operation_id="update_detection_type",
    summary="Update Detection Type",
    response_description="Updated detection type detail",
)
async def update_detection_type(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    payload: DetectionTypeUpdatePayload,
    org_id: str = Path(..., description="Organization ID"),
    agrifield_id: str = Path(..., description="Agriculture Field ID"),
    detection_type_id: str = Path(..., description="Detection Type ID"),
) -> DetectionType:
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    checker = SecurityChecker(CanManageOrganizationAgrifields)
    checker.check_object_permission(token_info, organization)

    agrifield_service = AgriFieldServices()
    agrifield_service.get(agrifield_id)

    detection_type_services = DetectionTypeServices()
    existing_type = detection_type_services.get(detection_type_id)
    if existing_type.agrifieldId != agrifield_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection type not found"
        )
    detection_type = detection_type_services.update(detection_type_id, payload)
    return detection_type


@router.delete(
    "/{detection_type_id}",
    operation_id="delete_detection_type",
    summary="Delete Detection Type",
    response_description="Deletion status",
)
async def delete_detection_type(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    org_id: str = Path(..., description="Organization ID"),
    agrifield_id: str = Path(..., description="Agriculture Field ID"),
    detection_type_id: str = Path(..., description="Detection Type ID"),
) -> StatusResponse:
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    checker = SecurityChecker(CanManageOrganizationAgrifields)
    checker.check_object_permission(token_info, organization)

    agrifield_service = AgriFieldServices()
    agrifield_service.get(agrifield_id)

    detection_type_services = DetectionTypeServices()
    existing_type = detection_type_services.get(detection_type_id)
    if existing_type.agrifieldId != agrifield_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection type not found"
        )
    detection_type_services.delete(detection_type_id)

    response = {"status": 200, "message": "Detection type deleted successfully"}
    response = StatusResponse(**response)
    return response
