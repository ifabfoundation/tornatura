from typing import Annotated, List

from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile

from core.permissions import IsAdmin, IsAuthenticated
from core.security import SecurityChecker
from core.serializers import (
    BbchScale,
    BbchScaleCreatePayload,
    BbchScaleDuplicatePayload,
    BbchScaleUpdatePayload,
    FileInfo,
    StatusResponse,
)
from core.services.bbch_scales_services import BbchScaleServices
from core.services.files_services import FileServices


router = APIRouter()


@router.get("", operation_id="list_bbch_scales", summary="List BBCH scales")
async def list_bbch_scales(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
) -> List[BbchScale]:
    return BbchScaleServices().list()


@router.post("", operation_id="create_bbch_scale", summary="Create BBCH scale")
async def create_bbch_scale(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    payload: BbchScaleCreatePayload,
) -> BbchScale:
    return BbchScaleServices().create(payload)


@router.post(
    "/thumbnails/upload",
    operation_id="upload_bbch_thumbnail",
    summary="Upload BBCH thumbnail",
)
async def upload_bbch_thumbnail(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    file: Annotated[UploadFile, File(description="BBCH thumbnail")],
) -> FileInfo:
    try:
        name = FileServices().upload_bbch_thumbnail(file)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return FileInfo(category="bbchs", name=name)


@router.post(
    "/{source_harvest_code}/duplicate",
    operation_id="duplicate_bbch_scale",
    summary="Duplicate and customize a BBCH scale",
)
async def duplicate_bbch_scale(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    payload: BbchScaleDuplicatePayload,
    source_harvest_code: str = Path(...),
) -> BbchScale:
    return BbchScaleServices().duplicate(source_harvest_code, payload.targetHarvestCode)


@router.get("/{harvest_code}", operation_id="get_bbch_scale", summary="Get BBCH scale")
async def get_bbch_scale(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    harvest_code: str = Path(...),
) -> BbchScale:
    return BbchScaleServices().get(harvest_code)


@router.put("/{harvest_code}", operation_id="update_bbch_scale", summary="Update BBCH scale")
async def update_bbch_scale(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    payload: BbchScaleUpdatePayload,
    harvest_code: str = Path(...),
) -> BbchScale:
    return BbchScaleServices().update(harvest_code, payload)


@router.delete("/{harvest_code}", operation_id="delete_bbch_scale", summary="Delete BBCH scale")
async def delete_bbch_scale(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    harvest_code: str = Path(...),
) -> StatusResponse:
    BbchScaleServices().delete(harvest_code)
    return StatusResponse(status=200, message="BBCH scale deleted successfully")
