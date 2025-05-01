from enum import Enum
from pydantic import BaseModel
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
    organizations: List[UserOrgananizationMembership] = []
    creationTime: int

class Point(BaseModel):
    lng: float
    lat: float

class AgriField(BaseModel):
    id: str
    name: str
    description: str
    map: List[Point]
    orgId: str
    creationTime: int
    lastUpdateTime: int

class Contacts(BaseModel):
    email: str
    phone : str

class Organization(BaseModel):
    orgId: str
    name: str
    description: str
    logo: str
    cover: str
    contacts: Contacts
    creationTime: int
    lastUpdateTime: int

class Detection(BaseModel):
    id: str
    agrifieldId: str
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
    description: str
    contacts: Contacts

class OrganizationUpdatePayload(BaseModel):
    description: str
    logo: FileInfo
    cover: FileInfo
    contacts: Contacts
    
class AgriFieldMutationPayload(BaseModel):
    name: str
    description: str
    map : List[Point]

class DetectionMutationPayload(BaseModel):
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
    organization: Optional[OrganizationCreatePayload] = None

class FeedbackCreatePayload(BaseModel):
    category: FeedbackCategoryEnum
    feedback: str
    author: str
