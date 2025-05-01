from typing import Annotated
from fastapi import APIRouter, Depends, Query

from core.permissions import IsAdmin, IsAuthenticated
from core.security import SecurityChecker
from core.serializers import Feedback, FeedbackCreatePayload, PaginatedResponse
from core.services.feedback_services import FeedbackServices
from core.utils import paginate


router = APIRouter()


@router.get(
    "",
    operation_id="list_feebacks",
    summary="List Feedbacks",
    response_description="Feedback List",
)
async def list_feebacks(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAdmin))],
    page: int = Query(1, ge=1, description="Page number"), 
    limit: int= Query(25, ge=25, le=1000, description="Items per page"),
    ) -> PaginatedResponse:

    feedback_services = FeedbackServices()
    data = feedback_services.list()
    total_count = len(data)
    data = paginate(data, page, limit)
    return PaginatedResponse(data=data, total=total_count, page=page, limit=limit)


@router.post(
    "",
    operation_id="add_feedback",
    summary="Add Feedback",
    response_description="Feedback Info",
)
async def add_feedback(
    token_info: Annotated[dict, Depends(SecurityChecker(IsAuthenticated))],
    payload: FeedbackCreatePayload, 
    ) -> Feedback:
    feedback_services = FeedbackServices()
    feedback = feedback_services.create(payload)
    return feedback
