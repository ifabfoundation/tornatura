from fastapi import APIRouter
from core.api.v1.agrifields import router as agrifields_router
from core.api.v1.users import router as users_router
from core.api.v1.organizations import router as organizations_router
from core.api.v1.detections import router as detections_router
from core.api.v1.detection_types import router as detection_types_router
from core.api.v1.files import router as files_router
from core.api.v1.feedback import router as feedbacks_router
from core.api.v1.invitations import router as invitations_router
from core.api.v1.observation_types import router as observation_types_router


router = APIRouter()

# Include feature routers with their specific prefixes
router.include_router(
    agrifields_router,
    prefix="/organizations/{org_id}/agrifields",
    tags=["AgriFields"]
)

router.include_router(
    files_router,
    prefix="/organizations/{org_id}/files",
    tags=["Files"]
)

router.include_router(
    organizations_router,
    prefix="/organizations",
    tags=["Organizations"]
)

router.include_router(
    detections_router,
    prefix="/organizations/{org_id}/agrifields/{agrifield_id}/detections",
    tags=["Detections"]
)

router.include_router(
    detection_types_router,
    prefix="/organizations/{org_id}/agrifields/{agrifield_id}/detection-types",
    tags=["DetectionTypes"]
)

router.include_router(
    observation_types_router,
    prefix="/observation-types",
    tags=["ObservationTypes"]
)


router.include_router(
    users_router,
    prefix="/users",
    tags=["Users"]
)

router.include_router(
    feedbacks_router,
    prefix="/feedbacks",
    tags=["Feedbacks"]
)

router.include_router(
    invitations_router,
    prefix="",
    tags=["Invitations"]
)
