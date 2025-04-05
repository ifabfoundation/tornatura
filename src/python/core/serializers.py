from pydantic import BaseModel
from typing import Any, List, Optional


class ErrorResponse(BaseModel):
    status: int
    detail: str | dict

class FileInfo(BaseModel):
    category: str
    name: str

class UserOrgananizationMembership(BaseModel):
    id: str
    name : str
    roles: List[str]

class User(BaseModel):
    id: Optional[str] = None
    firstName: str
    lastName: str
    email: str
    emailVerified: bool
    enabled: bool
    accountType: Optional[str] = None
    organizations: Optional[List[UserOrgananizationMembership]] = None
    creationTime: int

class Point(BaseModel):
    lng: float
    lat: float

class AgriField(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    map: List[Point]
    orgId: str
    creationTime: int
    lastUpdateTime: int

class Organization(BaseModel):
    orgId: Optional[str] = None
    name: str
    description: str
    logo: str
    cover: str
    creationTime: int
    lastUpdateTime: int

class Survey(BaseModel):
    id: Optional[str] = None
    agrifieldId: str
    name: str
    type: str
    position: Point
    photos: List[str]
    note: str
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
    logo: FileInfo
    cover: FileInfo

class OrganizationUpdatePayload(BaseModel):
    description: str
    logo: FileInfo
    cover: FileInfo

class AgriFieldMutationPayload(BaseModel):
    name: str
    description: str
    map : List[Point]

class SurveyMutationPayload(BaseModel):
    name: str
    type: str
    position: Point
    photos: List[FileInfo]
    note: str

