import os
from typing import Annotated, List
from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, Request, UploadFile, status
from core.permissions import IsAdmin, IsAuthenticated
from core.security import SecurityChecker
from core.serializers import AccountTypeEnum, ErrorResponse, FileInfo, PaginatedResponse, StatusResponse, User, UserCreatePayload, UserUpdatePayload
from core.services.files_services import FileServices
from core.services.organizations_services import OrganizationCustomRole, OrganizationDefaultRole, OrganizationServices
from core.services.users_services import ClientRole, UserServices
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
    user_services = UserServices()
    user = user_services.get(token_info)
    return user


@router.post(
    "/registration",
    operation_id="register_user",
    summary="User Registration",
    response_description="Operation status",
    status_code=status.HTTP_201_CREATED,
    responses={
        422: {
            "description": "Validation error",
            "model": ErrorResponse,
        },
        400: {
            "description": "Bad Request",
            "model": ErrorResponse,
        },
    }
)
async def user_registration(
    payload: UserCreatePayload,
    request: Request
    ) -> StatusResponse:
    user_services = UserServices()
    organization_services = OrganizationServices()

    if payload.accountType == AccountTypeEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with admin account type cannot be created",
        )

    if user_services.exists_by_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with the same email already exists",
        )
    
    if (payload.accountType == AccountTypeEnum.standard 
        and payload.organization is not None 
        and organization_services.is_organization_exists(payload.organization.name)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with the same name already exists",
        )
    
    user = user_services.create(payload)
    if payload.accountType == AccountTypeEnum.standard and payload.organization is not None:
        user_services.assign_role(user.id, ClientRole.CompanyOwner)
        organization = organization_services.create(payload.organization)
        # assign organization roles to the user
        organization_services.add_member(user_id=user.id, org_id=organization.orgId)
        organization_services.assign_role(user_id=user.id, org_id=organization.orgId, role=OrganizationDefaultRole.ManageOrganization)
        organization_services.assign_role(user_id=user.id, org_id=organization.orgId, role=OrganizationDefaultRole.ManageMembers)
        organization_services.assign_role(user_id=user.id, org_id=organization.orgId, role=OrganizationCustomRole.ManageAgrifields)
        organization_services.assign_role(user_id=user.id, org_id=organization.orgId, role=OrganizationCustomRole.ManageDataFiles)
        organization_services.assign_role(user_id=user.id, org_id=organization.orgId, role=OrganizationDefaultRole.ManageInvitations)
    
    
    return StatusResponse(status=201, message="User created successfully")


@router.put(
    "/me/update",
    operation_id="update_user",
    summary="Update current user",
    response_description="User Info",
    status_code=status.HTTP_200_OK,
    responses={
        422: {
            "description": "Validation error",
            "model": ErrorResponse,
        },
        400: {
            "description": "Bad Request",
            "model": ErrorResponse,
        },
    }
)
async def update_user(
    payload: UserUpdatePayload,
    request: Request,
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))]
    ) -> User:
    user_services = UserServices()
    user = user_services.update(token_info, payload)
    print("User updated successfully")

    return user


@router.post(
    "/me/avatar",
    operation_id="user_avatar_upload",
    summary="User Avatar Upload",
    response_description="User Avatar Url",
)
async def upload_user_avatar(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    avatar:  Annotated[
        UploadFile, File(description="avatar as UploadFile")
    ],
    ) -> FileInfo:

    # Upload the file and get the file name
    file_services = FileServices()
    file_name = file_services.upload_avatar(token_info["sub"], avatar)

    # Update user's avatar in Keycloak
    user_services = UserServices()
    user_services.update_avatar(token_info, file_name)

    # Create a FileInfo object with the uploaded file name
    file_info = FileInfo(name=file_name, category="media")

    return file_info
