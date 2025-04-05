from typing import Annotated, List
from fastapi import APIRouter, Depends, Path, Query
from core.permissions import IsAdmin, IsAuthenticated
from core.security import SecurityChecker
from core.serializers import ErrorResponse, PaginatedResponse, User
from core.services.users_services import UserServices
from core.utils import paginate


router = APIRouter()


@router.get(
    "",
    operation_id="list_users",
    summary="List Users",
    response_description="List of users",
)
async def list_users(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    page: int = Query(1, ge=1, description="Page number"), 
    limit: int= Query(25, ge=25, le=1000, description="Items per page"),
    ) -> PaginatedResponse:

    user_services = UserServices()
    data = user_services.list()
    total_count = len(data)
    data = paginate(data, page, limit)
    return PaginatedResponse(data=data, total=total_count, page=page, limit=limit)


@router.get(
    "/me/info",
    operation_id="user_info",
    summary="Current User Info",
    response_description="User Info",
)
async def user_info(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))]
    ) -> User:
    print(token_info)
    user_services = UserServices()
    user = user_services.get(token_info)
    return user

