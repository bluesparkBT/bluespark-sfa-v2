from typing import Optional, Annotated, List
from pydantic import Field
from sqlmodel import SQLModel
from utils.util_functions import validate_name, validate_phone_number, validate_email
from pydantic import AfterValidator, BaseModel, ValidationError
from datetime import datetime
from models.Account import IdType, OrganizationType, AccessPolicy
from starlette.requests import Request
from starlette.responses import JSONResponse
from pydantic import EmailStr, BaseModel
from typing import List

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
    # old_password: Optional[str]
    # password: Optional[str]

class OrganizationView(BaseModel):
    name: Annotated [ str, AfterValidator( validate_name) ]
    owner_name: Annotated [ str, AfterValidator( validate_name) ]
    description: Optional [Annotated [ str, AfterValidator( validate_name) ] ]   
    logo_image: Optional[str]
    parent_organization: Optional[int] = None
    organization_type: OrganizationType
    inheritance_group: Optional[int] = None
    address:Optional[int] = None
    landmark:Optional[str] = None
    latitude: Optional[float | str | None] = None
    longitude: Optional[float | str | None] = None

class UpdateOrganizationView(BaseModel):
    id: Optional[int | None]
    name: Annotated [ str, AfterValidator( validate_name) ]
    owner_name: Annotated [ str, AfterValidator( validate_name) ]
    description: Optional [Annotated [ str, AfterValidator( validate_name) ] ]   
    logo_image: Optional[str]
    parent_organization: Optional[int] = None
    organization_type: OrganizationType
    inheritance_group: Optional[int] = None
    address:Optional[int] = None
    landmark:Optional[str] = None
    latitude: Optional[int | str] = None
    longitude: Optional[int | str] = None

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
    
class RoleView(BaseModel):
    id: Optional [int ]
    name: Annotated [ str, AfterValidator( validate_name) ]
    module: str 
    policy: Optional[str] = None
    
# class UpdateRoleView(BaseModel):
#     id: Optional[int]
#     name: Annotated [ str, AfterValidator( validate_name) ]
#     # organization: int
#     module: str
#     policy: Optional[AccessPolicy] = None


class EmailSchema(BaseModel):
#    email: List[EmailStr]  
     username: str
