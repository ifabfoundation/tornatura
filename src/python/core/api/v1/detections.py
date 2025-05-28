from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query
from core.permissions import CanManageOrganizationAgrifields, CanViewOrganizationAgrifields, IsAuthenticated
from core.security import SecurityChecker
from core.serializers import ErrorResponse, PaginatedResponse, Detection, DetectionMutationPayload
from core.services.agrifields_services import AgriFieldServices
from core.services.organizations_services import OrganizationServices
from core.services.detections_services import DetectionServices
from core.utils import paginate


router = APIRouter()


@router.get(
    "",
    operation_id="list_detections",
    summary="List Detections",
    response_description="List detections for an agriculture field",
)
async def list_detections(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    org_id: str = Path(..., description="Organization ID"), 
    agrifield_id: str = Path(..., description="Agriculture Field ID"), 
    page: int = Query(1, ge=1, description="Page number"), 
    limit: int = Query(25, ge=1, le=1000, description="Items per page"),
) -> PaginatedResponse:
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    # Check object-level permissions
    checker = SecurityChecker(CanViewOrganizationAgrifields)
    checker.check_object_permission(token_info, organization)

    agrifield_service = AgriFieldServices()
    agrifield_service.get(agrifield_id)

    detection_service = DetectionServices()
    data = detection_service.list(agrifield_id)
    count = len(data)
    data = paginate(data, page, limit)
    return PaginatedResponse(data=data, total=count, page=page, limit=limit)


@router.post(
    "",
    operation_id="create_detection",
    summary="Create Detection",
    response_description="Detection detail",
)
async def create_detection(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    payload: DetectionMutationPayload,
    org_id: str = Path(..., description="Organization ID"), 
    agrifield_id: str = Path(..., description="Agriculture Field ID"),
) -> Detection:
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    # Check object-level permissions
    checker = SecurityChecker(CanManageOrganizationAgrifields)
    checker.check_object_permission(token_info, organization)

    agrifield_service = AgriFieldServices()
    agrifield_service.get(agrifield_id)

    detection_service = DetectionServices()
    detection = detection_service.create(agrifield_id, payload)
    return detection


@router.put(
    "/{detection_id}",
    operation_id="update_detection",
    summary="Update Detection",
    response_description="New Detection detail",
)
async def update_detection(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    payload: DetectionMutationPayload,
    org_id: str = Path(..., description="Organization ID"), 
    agrifield_id: str = Path(..., description="Agriculture Field ID"),
    detection_id: str = Path(..., description="Detection Field ID"),
) -> Detection:
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    # Check object-level permissions
    checker = SecurityChecker(CanManageOrganizationAgrifields)
    checker.check_object_permission(token_info, organization)

    agrifield_service = AgriFieldServices()
    agrifield_service.get(agrifield_id)

    detection_service = DetectionServices()
    detection = detection_service.update(detection_id, payload)
    return detection