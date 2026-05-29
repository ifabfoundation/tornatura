from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from core.permissions import IsAdmin, IsAuthenticated
from core.security import SecurityChecker
from core.serializers import (
    HarvestType,
    HarvestTypeCreatePayload,
    HarvestTypeUpdatePayload,
    PaginatedResponse,
    StatusResponse,
)
from core.services.harvest_types_services import HarvestTypeServices
from core.utils import paginate


router = APIRouter()


@router.get(
    "",
    operation_id="list_harvest_types",
    summary="List Harvest Types",
    response_description="List of harvest types",
)
async def list_harvest_types(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=1000, description="Items per page"),
    active: bool | None = Query(None, description="Filter by active state"),
    include_inactive: bool = Query(False, description="Include inactive harvest types"),
) -> PaginatedResponse:
    harvest_type_services = HarvestTypeServices()
    data = harvest_type_services.list(active=active, include_inactive=include_inactive)
    total_count = len(data)
    data = paginate(data, page, limit)
    return PaginatedResponse(data=data, total=total_count, page=page, limit=limit)


@router.post(
    "",
    operation_id="create_harvest_type",
    summary="Create Harvest Type",
    response_description="Harvest type detail",
)
async def create_harvest_type(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    payload: HarvestTypeCreatePayload,
) -> HarvestType:
    harvest_type_services = HarvestTypeServices()
    return harvest_type_services.create(payload)


@router.get(
    "/{harvest_type_id}",
    operation_id="get_harvest_type",
    summary="Get Harvest Type",
    response_description="Harvest type detail",
)
async def get_harvest_type(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    harvest_type_id: str = Path(..., description="Harvest Type ID"),
) -> HarvestType:
    harvest_type_services = HarvestTypeServices()
    return harvest_type_services.get(harvest_type_id)


@router.put(
    "/{harvest_type_id}",
    operation_id="update_harvest_type",
    summary="Update Harvest Type",
    response_description="Updated harvest type detail",
)
async def update_harvest_type(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    payload: HarvestTypeUpdatePayload,
    harvest_type_id: str = Path(..., description="Harvest Type ID"),
) -> HarvestType:
    harvest_type_services = HarvestTypeServices()
    return harvest_type_services.update(harvest_type_id, payload)


@router.delete(
    "/{harvest_type_id}",
    operation_id="delete_harvest_type",
    summary="Delete Harvest Type",
    response_description="Deletion status",
)
async def delete_harvest_type(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    harvest_type_id: str = Path(..., description="Harvest Type ID"),
) -> StatusResponse:
    harvest_type_services = HarvestTypeServices()
    harvest_type_services.delete(harvest_type_id)
    return StatusResponse(status=200, message="Harvest type deleted successfully")
