from typing import Optional, Annotated, List
from pydantic import Field
from sqlmodel import SQLModel
from utils.util_functions import validate_name, validate_phone_number, validate_email
from pydantic import AfterValidator, BaseModel, ValidationError
from datetime import datetime
from models.Account import IdType, OrganizationType, AccessPolicy

class SuperAdminView(BaseModel):
    full_name: Annotated [ str, AfterValidator( validate_name) ]
    username: Annotated [ str, AfterValidator( validate_name) ]
    email: Annotated [ str, AfterValidator( validate_email) ] | None
    password: str
    
class UpdateSuperAdminView(BaseModel):
    id: Optional[int]
    full_name: Annotated [ str, AfterValidator( validate_name) ]
    username: Annotated [ str, AfterValidator( validate_name) ]
    email: Annotated [ str, AfterValidator( validate_email) ] | None
    phone_number: Optional [Annotated [ str, AfterValidator( validate_phone_number) ] | None] 
    old_password: str
    new_password: str
    role: Optional[int]
    scope_group: Optional[int]
    
class UserAccountView(BaseModel):
    full_name: Annotated [ str, AfterValidator( validate_name) ]
    username: Annotated [ str, AfterValidator( validate_name) ]
    email: Annotated [ str, AfterValidator( validate_email) ] | None
    phone_number: Optional [Annotated [ str, AfterValidator( validate_phone_number) ] | None] 
    role: Optional[int]
    scope: str
    scope_group: Optional[int]
    organization: Optional[int]
    gender: Optional[str] 
    address : Optional[int| str| None]
    # salary: Optional[float] = None
    # position: Optional[str] = None
    # date_of_birth: Optional[datetime] = None
    # date_of_joining: Optional[datetime] = None
    manager: Optional[int] = None
    # image: Optional[str] = None
    # id_type: Optional[IdType] = None
    # id_number: Optional[str] = None
    address: Optional[int]

class UpdateUserAccountView(BaseModel):
    id: Optional[int] = None
    full_name: Annotated [ str, AfterValidator( validate_name) ]
    username: Annotated [ str, AfterValidator( validate_name) ]
    email: Annotated [ str, AfterValidator( validate_email) ] | None
    phone_number: Optional [Annotated [ str, AfterValidator( validate_phone_number) ] | None] 
    organization: Optional[int]
    role: Optional[int]
    scope: str
    scope_group: Optional[int]
    gender: Optional[str] 
    # salary: Optional[float] = None
    # position: Optional[str] = None
    # date_of_birth: Optional[datetime] = None
    # date_of_joining: Optional[datetime] = None 
    manager: Optional[int] = None
    # image: Optional[str] = None
    # id_type: Optional[IdType] = None
    # id_number: Optional[str] = None
    address : Optional[int| str| None]

class OrganizationView(BaseModel):
    id: Optional[int | None]
    name: Annotated [ str, AfterValidator( validate_name) ]
    owner_name: Annotated [ str, AfterValidator( validate_name) ]
    organization_type: OrganizationType
    logo_image: Optional[str]
    description: Optional [Annotated [ str, AfterValidator( validate_name) ] ]   
    parent_organization: Optional[int] = None
    address:Optional[int] = None
    latitude: Optional[int] = None
    longitude: Optional[int] = None
    inheritance_group: Optional[int] = None
    
class TenantView(BaseModel):
    name: Annotated [ str, AfterValidator( validate_name) ]
    owner_name: Annotated [ str, AfterValidator( validate_name) ]
    logo_image: Optional[str]
    description: Annotated [ str, AfterValidator( validate_name) ]    
    parent_organization: int
    address: Optional[int] = None
    # geolocation_id: Optional[int] = None

class ScopeGroupView(BaseModel):
    name: Annotated [ str, AfterValidator( validate_name) ]
    hidden: List[int]
    
class UpdateScopeGroupView(BaseModel):
    id: Optional[int]
    name: Annotated [ str, AfterValidator( validate_name) ]
    hidden: List[int]
    
class RoleCreation(BaseModel):
    name: Annotated [ str, AfterValidator( validate_name) ]
    organization: int


class RoleModulePermissionCreation(BaseModel):
    role: int
    module: str | type
    access_policy: Optional[AccessPolicy] = None
