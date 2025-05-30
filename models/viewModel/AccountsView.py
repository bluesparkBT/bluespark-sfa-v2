from typing import Optional
from typing import Annotated
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


class UserAccountView(BaseModel):
    full_name: Annotated [ str, AfterValidator( validate_name) ]
    username: Annotated [ str, AfterValidator( validate_name) ]
    email: Annotated [ str, AfterValidator( validate_email) ] | None
    phone_number: Optional [Annotated [ str, AfterValidator( validate_phone_number) ] | None] 
    role_id: Optional[int]
    scope: str
    scope_group_id: Optional[int]
    organization_id: Optional[int]
    gender: Optional[str] 
    address : Optional[int| str| None]
    manager_id: Optional[int] = None
    salary: Optional[float] = None
    position: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    date_of_joining: Optional[datetime] = None
    image: Optional[str] = None
    id_type: Optional[IdType] = None
    id_number: Optional[str] = None
    hashedPassword: Optional[str] = None
        
class OrganizationView(BaseModel):
    name: Annotated [ str, AfterValidator( validate_name) ]
    owner_name: Annotated [ str, AfterValidator( validate_name) ]
    organization_type: OrganizationType
    description: Annotated [ str, AfterValidator( validate_name) ]    
    parent_id: Optional[int] = None
    address_id: Optional[int] = None
    geolocation_id: Optional[int] = None
    inheritance_group: Optional[int] = None

class ScopeGroupCreation(BaseModel):
    name: Annotated [ str, AfterValidator( validate_name) ]

class RoleCreation(BaseModel):
    name: Annotated [ str, AfterValidator( validate_name) ]
    organization_id: int

class RoleModulePermissionCreation(BaseModel):
    role_id: int
    module: str | type
    access_policy: Optional[AccessPolicy] = None





class EmailSchema(BaseModel):
#    email: List[EmailStr]  
     username: str
