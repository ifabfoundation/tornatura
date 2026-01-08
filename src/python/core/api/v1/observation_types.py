from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query

from core.permissions import IsAdmin, IsAuthenticated
from core.security import SecurityChecker
from core.serializers import (
    ObservationType,
    ObservationTypeCreatePayload,
    ObservationTypeUpdatePayload,
    PaginatedResponse,
    StatusResponse,
)
from core.services.observation_types_services import ObservationTypeServices
from core.utils import paginate


router = APIRouter()


@router.get(
    "",
    operation_id="list_observation_types",
    summary="List Observation Types",
    response_description="List of observation types",
)
async def list_observation_types(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=1000, description="Items per page"),
) -> PaginatedResponse:
    observation_type_services = ObservationTypeServices()
    data = observation_type_services.list()
    total_count = len(data)
    data = paginate(data, page, limit)
    return PaginatedResponse(data=data, total=total_count, page=page, limit=limit)


@router.post(
    "",
    operation_id="create_observation_type",
    summary="Create Observation Type",
    response_description="Observation type detail",
)
async def create_observation_type(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    payload: ObservationTypeCreatePayload,
) -> ObservationType:
    observation_type_services = ObservationTypeServices()
    observation_type = observation_type_services.create(payload)
    return observation_type


@router.get(
    "/{observation_type_id}",
    operation_id="get_observation_type",
    summary="Get Observation Type",
    response_description="Observation type detail",
)
async def get_observation_type(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    observation_type_id: str = Path(..., description="Observation Type ID"),
) -> ObservationType:
    observation_type_services = ObservationTypeServices()
    observation_type = observation_type_services.get(observation_type_id)
    return observation_type


@router.put(
    "/{observation_type_id}",
    operation_id="update_observation_type",
    summary="Update Observation Type",
    response_description="Updated observation type detail",
)
async def update_observation_type(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    payload: ObservationTypeUpdatePayload,
    observation_type_id: str = Path(..., description="Observation Type ID"),
) -> ObservationType:
    observation_type_services = ObservationTypeServices()
    observation_type = observation_type_services.update(observation_type_id, payload)
    return observation_type


@router.delete(
    "/{observation_type_id}",
    operation_id="delete_observation_type",
    summary="Delete Observation Type",
    response_description="Deletion status",
)
async def delete_observation_type(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    observation_type_id: str = Path(..., description="Observation Type ID"),
) -> StatusResponse:
    observation_type_services = ObservationTypeServices()
    observation_type_services.delete(observation_type_id)

    response = {"status": 200, "message": "Observation type deleted successfully"}
    response = StatusResponse(**response)
    return response
