from enum import Enum
from pydantic import BaseModel, EmailStr
from typing import Any, List, Optional


class ErrorResponse(BaseModel):
    status: int
    detail: str | dict

class StatusResponse(BaseModel):
    status: int
    message: str

class FileInfo(BaseModel):
    category: str
    name: str

class UserOrgananizationMembership(BaseModel):
    id: str
    name : str
    roles: List[str]

class AccountTypeEnum(str, Enum):
    admin = 'Admin'
    agronomist = 'Agronomist'
    standard = 'Standard'

class FeedbackCategoryEnum(str, Enum):
    NewFeature = 'New Feature'
    bugFixing = 'Bug Fixing'
    Improvement = 'Improvement'
    Other = 'Other'


class User(BaseModel):
    id: str
    firstName: str
    lastName: str
    email: str
    emailVerified: bool
    enabled: bool
    accountType: AccountTypeEnum
    phone: str
    piva: str
    avatar: str
    organizations: List[UserOrgananizationMembership] = []
    creationTime: int

class OrganizationMember(BaseModel):
    user: User
    role: str

class Point(BaseModel):
    lng: float
    lat: float

class DetectionType(BaseModel):
    id: str
    agrifieldId: str
    observationTypeId: str
    creationTime: int

class ObservationCounter(BaseModel):
    counterName: str
    counterValue: float

class ObservationType(BaseModel):
    id: str
    typology: str
    method: str
    category: str
    locationAndScoreInstructions: str
    observationHint: str
    observationType: str
    rangeMin: Optional[float] = None
    rangeMax: Optional[float] = None
    rangeLabels: List[str] = []
    counters: List[str] = []
    creationTime: int

class ObservationData(BaseModel):
    rangeValue: Optional[float] = None
    counters: List[ObservationCounter] = []

class ObservationPoint(BaseModel):
    position: Point
    data: ObservationData

class DetectionData(BaseModel):
    bbch: str
    notes: str
    photos: List[str]
    points: List[ObservationPoint]

class DetectionDataPayload(BaseModel):
    bbch: str
    notes: str
    photos: List[FileInfo]
    points: List[ObservationPoint]

class DetectionTypeCreatePayload(BaseModel):
    observationTypeId: str

class DetectionTypeUpdatePayload(BaseModel):
    observationTypeId: Optional[str] = None

class ObservationTypeCreatePayload(BaseModel):
    typology: str
    method: str
    category: str
    locationAndScoreInstructions: str
    observationHint: str = "Valuta l'intensità del sintomo"
    observationType: str
    rangeMin: Optional[float] = None
    rangeMax: Optional[float] = None
    rangeLabels: List[str] = []
    counters: List[str] = []

class ObservationTypeUpdatePayload(BaseModel):
    typology: Optional[str] = None
    method: Optional[str] = None
    category: Optional[str] = None
    locationAndScoreInstructions: Optional[str] = None
    observationHint: Optional[str] = None
    observationType: Optional[str] = None
    rangeMin: Optional[float] = None
    rangeMax: Optional[float] = None
    rangeLabels: Optional[List[str]] = None
    counters: Optional[List[str]] = None

class AgriField(BaseModel):
    id: str
    name: str
    description: str
    harvest: str
    area: float
    plants: int
    variety: str
    rotation: str
    year: Optional[str] = None
    irrigation: str
    grassing: str
    weaving: str
    map: List[Point]
    orgId: str
    creationTime: int
    lastUpdateTime: int

class Contacts(BaseModel):
    email: str
    phone : str

class Office(BaseModel):
    state: str
    city : str

class Organization(BaseModel):
    orgId: str
    name: str
    piva: str
    logo: str
    cover: str
    contacts: Contacts
    creationTime: int
    lastUpdateTime: int

class Detection(BaseModel):
    id: str
    agrifieldId: str
    detectionTime: int
    detectionTypeId: str
    detectionData: DetectionData
    creationTime: int
    lastUpdateTime: int

class Feedback(BaseModel):
    id: str
    category: FeedbackCategoryEnum
    feedback: str
    author: str
    creationTime: int
    lastUpdateTime: int

class PaginatedResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[Any]
    
class OrganizationCreatePayload(BaseModel):
    name: str
    piva: str
    contacts: Contacts

class OrganizationUpdatePayload(BaseModel):
    name: Optional[str] = None
    piva: Optional[str] = None
    logo:  Optional[FileInfo] = None
    cover: Optional[FileInfo] = None
    contacts: Optional[Contacts] = None
    
class AgriFieldMutationPayload(BaseModel):
    name: str
    description: str
    map : List[Point]
    harvest: str
    area: float
    plants: int
    variety: str
    rotation: str
    year: Optional[str] = None
    irrigation: str
    grassing: str
    weaving: str

class DetectionMutationPayload(BaseModel):
    detectionTime: int
    detectionTypeId: str
    detectionData: DetectionDataPayload

class UserCreatePayload(BaseModel):
    firstName: str
    lastName: str
    email: str
    accountType: AccountTypeEnum
    phone: str
    piva: Optional[str] = None
    organization: Optional[OrganizationCreatePayload] = None
    questionnaire: Optional[dict[str, Any]] = None

class UserUpdatePayload(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phone: Optional[str] = None

class FeedbackCreatePayload(BaseModel):
    category: FeedbackCategoryEnum
    feedback: str
    author: str

# Invitation serializers
class InvitationCreatePayload(BaseModel):
    """Payload for creating an invitation"""
    email: EmailStr
    role: str
    orgId: Optional[str] = None  # Optional - null when agronomist invites non-existent company owner

class Invitation(BaseModel):
    """Complete invitation model with all fields"""
    id: str
    email: str
    orgId: Optional[str] = None  # Optional - null when agronomist invites non-existent company owner
    organization: Optional[Organization] = None  # Optional - null when agronomist invites non-existent company owner
    inviterId: str
    role: str
    token: str
    status: str
    expiresAt: int
    acceptedAt: Optional[int] = None
    deleted: bool
    creationTime: int
    lastUpdateTime: int


    class Config:
        from_attributes = True

class InvitationPublic(BaseModel):
    """Public invitation info (without sensitive data like full token in some contexts)"""
    id: str
    email: str
    role: str
    status: str
    organization: Optional[Organization] = None  # Optional - null when agronomist invites non-existent company owner
    inviter: User
    expiresAt: int
    creationTime: int

class InvitationAcceptPayload(BaseModel):
    """Payload for accepting invitation"""
    token: str
    orgId: Optional[str] = None  # Required when company owner accepts invitation from agronomist

class InvitationValidateResponse(BaseModel):
    """Response for token validation"""
    valid: bool
    invitation: Optional[InvitationPublic] = None
    error: Optional[str] = None


class FormTemplateRenderPayload(BaseModel):
    data: dict[str, str]
