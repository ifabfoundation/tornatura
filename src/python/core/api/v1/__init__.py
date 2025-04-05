from fastapi import APIRouter
from core.api.v1.agrifields import router as agrifields_router
from core.api.v1.users import router as users_router
from core.api.v1.organizations import router as organizations_router
from core.api.v1.surveys import router as surveys_router  


router = APIRouter()

# Include feature routers with their specific prefixes
router.include_router(
    organizations_router,
    prefix="/organizations",
    tags=["Organizations"]
)

router.include_router(
    agrifields_router,
    prefix="/organizations/{org_id}/agrifields",
    tags=["AgriFields"]
)

router.include_router(
    surveys_router,
    prefix="/organizations/{org_id}/agrifields/{agrifield_id}/surveys",
    tags=["Surveys"]
)

router.include_router(
    users_router,
    prefix="/users",
    tags=["Users"]
)