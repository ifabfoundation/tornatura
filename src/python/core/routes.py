from typing import List
from fastapi import APIRouter, Depends
from core.permissions import IsAuthenticated
from core.security import SecurityChecker
from core.serializers import ErrorResponse, PaginatedResponse
from core.services.agrifields_services import AgriFieldServices
from core.utils import paginate


router = APIRouter()


@router.get(
    "/{companyId}/agrifields",
    tags=["AgriFields"],
    operation_id="list_agrifields",
    summary="List Agriculture Fields",
    response_description="List of Agriculture Fields",
    dependencies=[Depends(SecurityChecker(IsAuthenticated))]
)
async def search_agrifields(companyId: str, page: int =1, limit: int=25) -> PaginatedResponse:
    agrifield_service = AgriFieldServices()
    data = agrifield_service.list(companyId)
    total_count = len(data)
    data = paginate(data, page, limit)
    return PaginatedResponse(data=data, total=total_count, page=page, limit=limit)