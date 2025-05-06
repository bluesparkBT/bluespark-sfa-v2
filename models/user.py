from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
from datetime import  datetime
from typing import List, Optional, Self
from pydantic import Base64Bytes, model_validator, validate_email



class Gender(str, Enum):
    """
    Enum Class representing gender options.

    This enumeration provides a predefined set of gender options for use in the system.
    """

    Male = "Male"
    Female = "Female"


class IdType(str, Enum):
    """
    Enum Class representing identification types.

    This enumeration provides a predefined set of identification types for use in the system.
    """

    national_id = "National ID"
    kebele = "Kebele ID"
    yellow_card = "Yellow Card"
    birth_certificate = "Birth Certificate"
    school_certificate = "School Certificate"
    passport = "Passport"
    driving_license = "Driving License"
    school_id = "School ID"

class Scope(str, Enum):
    managerial_scope = "Managerial scope"
    personal_scope = "Personal scope"


class ScopeGroupOrganizationLink(SQLModel, table=True):
    __tablename__ = "scope_group_organization"

    id: Optional[int] = Field(default=None, primary_key=True)
    scope_group_id: int =Field(foreign_key="scope_group.id", index=True)
    organization_id: int = Field(foreign_key="organization.id", index=True)

class ScopeGroup(SQLModel, table=True):
    __tablename__ = "scope_group"

    id: Optional[int] = Field(default=None, primary_key=True)
    scope_name: str = Field(index=True, unique=True)
    organizations: List["Organization"] = Relationship(back_populates="scope_groups",link_model=ScopeGroupOrganizationLink)


    users: Optional[List["User"]] = Relationship(back_populates="scope_group")

class UserRole(SQLModel, table=True):
    __tablename__ = "user_role"

    id: int = Field( primary_key=True)
    username: str
    email: str
    password_hash: str
    tenant_id: int = Field(foreign_key="tenant.id")
    role_id: int = Field(foreign_key="role.id")


class Role(SQLModel, table=True):
    __tablename__ = "role"

    id: int = Field( primary_key=True)
    name: str
    tenant_id: int = Field(foreign_key="tenant.id")

class Module(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str


class AccessPolicy(str, Enum):
    
    view = "view"
    edit = "edit"
    contribute = "contribute"
    manage = "manage"


class RoleModulePermission(SQLModel, table=True):
    id: int = Field( primary_key=True)
    role_id: int = Field(foreign_key="role.id")
    module_id: int = Field(foreign_key="module.id")
    permission: AccessPolicy = Field(sa_column_kwargs={"nullable": False})

class Tenant(SQLModel, table=True):
    __tablename__ = "tenant"
    id: int = Field( primary_key=True)
    name: str

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    fullname: str = Field(index=True)
    username: str = Field(unique=True, index=True)
    email: Optional[str] = Field(index=True)
    phone: Optional[str] = Field(default=None,index=True)
    hashedPassword: str
    date_of_birth: Optional[datetime] = Field(default=None)
    date_of_joining: Optional[datetime] = Field(default=None)
    salary: Optional[float] = Field(default=None)
    position: Optional[str] = Field(default=None)
    id_type: Optional[IdType] = Field(default=None)
    id_number: Optional[str] = Field(default=None)
    gender: Optional[Gender]
    manager_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    address_id: Optional[int] = Field(default=None, foreign_key="address.id", index=True)
    role_id: Optional[int] = Field(default=None, foreign_key="role.id")
    scope: Scope = Field(default=Scope.personal_scope)
    scope_group_id: Optional[int] = Field(default=None, foreign_key="scope_group.id")

    scope_group: Optional[ScopeGroup] = Relationship(back_populates="users")

    @model_validator(mode="after")
    def check(self) -> Self:

        if validate_email(self.email) is False:
            raise ValueError("Invalid email")

        return self

    


class SuperAdminUser(SQLModel, table=True):
    __tablename__ = "service_provider_user"

    id: Optional[int] = Field(default=None, primary_key=True)
    service_provider_company: Optional[int] = Field(default=None, foreign_key="organization.id", index=True)
    username: str = Field(unique=True, index=True)
    email: Optional[str] = Field(index=True)
    hashedPassword: str
    role_id: Optional[int] = Field(default=None, foreign_key="role.id")
    scope_group_id: Optional[int] = Field(default=None, foreign_key="scope_group.id")

    @model_validator(mode="after")
    def check(self) -> Self:

        if validate_email(self.email) is False:
            raise ValueError("Invalid email")

        return self

