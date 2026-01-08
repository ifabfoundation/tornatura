from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query

from core.permissions import IsAdmin, IsAuthenticated
from core.security import SecurityChecker
from core.serializers import (
    DetectionText,
    DetectionTextCreatePayload,
    DetectionTextUpdatePayload,
    PaginatedResponse,
    StatusResponse,
)
from core.services.detection_texts_services import DetectionTextServices
from core.utils import paginate


router = APIRouter()


@router.get(
    "",
    operation_id="list_detection_texts",
    summary="List Detection Texts",
    response_description="List of detection texts",
)
async def list_detection_texts(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=1000, description="Items per page"),
) -> PaginatedResponse:
    detection_text_services = DetectionTextServices()
    data = detection_text_services.list()
    total_count = len(data)
    data = paginate(data, page, limit)
    return PaginatedResponse(data=data, total=total_count, page=page, limit=limit)


@router.post(
    "",
    operation_id="create_detection_text",
    summary="Create Detection Text",
    response_description="Detection text detail",
)
async def create_detection_text(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    payload: DetectionTextCreatePayload,
) -> DetectionText:
    detection_text_services = DetectionTextServices()
    detection_text = detection_text_services.create(payload)
    return detection_text


@router.get(
    "/{detection_text_id}",
    operation_id="get_detection_text",
    summary="Get Detection Text",
    response_description="Detection text detail",
)
async def get_detection_text(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    detection_text_id: str = Path(..., description="Detection Text ID"),
) -> DetectionText:
    detection_text_services = DetectionTextServices()
    detection_text = detection_text_services.get(detection_text_id)
    return detection_text


@router.put(
    "/{detection_text_id}",
    operation_id="update_detection_text",
    summary="Update Detection Text",
    response_description="Updated detection text detail",
)
async def update_detection_text(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    payload: DetectionTextUpdatePayload,
    detection_text_id: str = Path(..., description="Detection Text ID"),
) -> DetectionText:
    detection_text_services = DetectionTextServices()
    detection_text = detection_text_services.update(detection_text_id, payload)
    return detection_text


@router.delete(
    "/{detection_text_id}",
    operation_id="delete_detection_text",
    summary="Delete Detection Text",
    response_description="Deletion status",
)
async def delete_detection_text(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    detection_text_id: str = Path(..., description="Detection Text ID"),
) -> StatusResponse:
    detection_text_services = DetectionTextServices()
    detection_text_services.delete(detection_text_id)

    response = {"status": 200, "message": "Detection text deleted successfully"}
    response = StatusResponse(**response)
    return response
