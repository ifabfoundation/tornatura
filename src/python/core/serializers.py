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
    rapresentative: str
    rapresentativeContact: str
    legalForm: str
    office: Office
    logo: str
    cover: str
    contacts: Contacts
    creationTime: int
    lastUpdateTime: int

class Detection(BaseModel):
    id: str
    agrifieldId: str
    detectionTime: int
    type: str
    position: Point
    photos: List[str]
    note: str
    details: dict
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
    rapresentative: str
    rapresentativeContact: str
    legalForm: str
    office: Office
    contacts: Contacts

class OrganizationUpdatePayload(BaseModel):
    rapresentative: Optional[str] = None
    rapresentativeContact: Optional[str] = None
    legalForm: Optional[str] = None
    office: Optional[Office] = None
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
    type: str
    position: Point
    photos: List[FileInfo]
    note: str
    details: dict

class UserCreatePayload(BaseModel):
    firstName: str
    lastName: str
    email: str
    accountType: AccountTypeEnum
    phone: str
    piva: Optional[str] = None
    organization: Optional[OrganizationCreatePayload] = None

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
