from typing import Annotated, List
from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile
from core.permissions import CanManageOrganization, CanManageOrganizationDataFiles, IsAdmin, IsAuthenticated
from core.security import SecurityChecker
from core.serializers import ErrorResponse, FileInfo
from core.services.files_services import FileServices
from core.services.organizations_services import OrganizationServices
from core.utils import paginate


router = APIRouter()


@router.post(
    "/{category}/upload",
    operation_id="upload_files",
    summary="Upload files",
    response_description="File Info",
)
async def upload_files(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    files:  Annotated[
        list[UploadFile], File(description="Multiple files as UploadFile")
    ],
    org_id: str = Path(..., description="Organization ID"), 
    category: str = Path(..., description="Category of the files"),
    ) -> List[FileInfo]:

    # Validate the category
    if category not in ["media", "data"]:
        raise HTTPException(status_code=400, detail="Invalid category. Must be 'media' or 'data'.")
  
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    # Check object-level permissions
    if category == "data":
        checker = SecurityChecker(CanManageOrganizationDataFiles)
    else:
        checker = SecurityChecker(CanManageOrganization)
    
    # Check if the user has permission to upload files
    checker.check_object_permission(token_info, organization)

    results = []
    file_services = FileServices()

    for file in files:
        # Upload the file and get the file name
        file_name = file_services.upload_file(org_id, category, file)
        
        # Create a FileInfo object with the uploaded file name
        file_info = FileInfo(name=file_name, category=category)
        results.append(file_info)

    return results

