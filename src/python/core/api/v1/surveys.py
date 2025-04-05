from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query
from core.permissions import CanManageOrganizationAgrifields, CanViewOrganizationAgrifields, IsAuthenticated
from core.security import SecurityChecker
from core.serializers import ErrorResponse, PaginatedResponse, Survey, SurveyMutationPayload
from core.services.agrifields_services import AgriFieldServices
from core.services.organizations_services import OrganizationServices
from core.services.surveys_services import SurveyServices
from core.utils import paginate


router = APIRouter()


@router.get(
    "",
    operation_id="list_surveys",
    summary="List Surveys",
    response_description="List of surveys for an agriculture field",
)
async def list_surveys(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    org_id: str = Path(..., description="Organization ID"), 
    agrifield_id: str = Path(..., description="Agriculture Field ID"), 
    page: int = Query(1, ge=1, description="Page number"), 
    limit: int = Query(25, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse:
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    # Check object-level permissions
    checker = SecurityChecker(CanViewOrganizationAgrifields)
    checker.check_object_permission(token_info, organization)

    agrifield_service = AgriFieldServices()
    agrifield_service.get(agrifield_id)

    survey_service = SurveyServices()
    data = survey_service.list(agrifield_id)
    count = len(data)
    data = paginate(data, page, limit)
    return PaginatedResponse(data=data, total=count, page=page, limit=limit)


@router.post(
    "",
    operation_id="create_survey",
    summary="Create Survey",
    response_description="Survey detail",
)
async def create_survey(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    payload: SurveyMutationPayload,
    org_id: str = Path(..., description="Organization ID"), 
    agrifield_id: str = Path(..., description="Agriculture Field ID"),
) -> Survey:
    organization_services = OrganizationServices()
    organization = organization_services.get(org_id)

    # Check object-level permissions
    checker = SecurityChecker(CanManageOrganizationAgrifields)
    checker.check_object_permission(token_info, organization)

    agrifield_service = AgriFieldServices()
    agrifield_service.get(agrifield_id)

    survey_service = SurveyServices()
    survey = survey_service.create(agrifield_id, payload)
    return survey
