from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
from datetime import  datetime
from typing import List, Optional, Self
from models.Location import Address, Location


class ScopeGroupLink(SQLModel, table=True):
    __tablename__ = "scope_group_link"

    id: Optional[int] = Field(default=None, primary_key=True)
    scope_group_id: int = Field(foreign_key="scope_group.id", index=True)
    organization_id: int = Field(foreign_key="organization.id", index=True)


class ScopeGroup(SQLModel, table=True):
    __tablename__ = "scope_group"

    id: Optional[int] = Field(default=None, primary_key=True)
    scope_name: str = Field(index=True, unique=True)
    organizations: List["Organization"] = Relationship(back_populates="scope_groups", link_model=ScopeGroupLink)

class OrganizationType(str, Enum):
    distributor = "Distributor"
    subagent = "SubAgent"
    retailer = "Retailer"
    company = "Company"

class Organization(SQLModel, table=True): 
    __tablename__ = "organization"

    id: Optional[int] = Field(default=None, primary_key=True)
    organization_name: str = Field(index=True)
    owner_name: Optional[str] = Field(default=None,index=True)
    logo_image: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None, index=True)
    organization_type: OrganizationType = Field(default=OrganizationType.company)
    parent_id: Optional[int] = Field(default=None,  foreign_key="organization.id")
    scope_groups: List["ScopeGroup"] = Relationship(
        back_populates="organizations",
        link_model=ScopeGroupLink
    )
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
    managerial_scope = "managerial_scope"
    personal_scope = "personal_scope"

class Role(SQLModel, table=True):
    __tablename__ = "role"

    id: int = Field(primary_key=True)
    name: str
    organization_id: int = Field(foreign_key="organization.id")
    permissions: List["RoleModulePermission"] = Relationship(back_populates="role")

class AccessPolicy(str, Enum):
    deny = "deny"
    view = "view"
    edit = "edit"
    contribute = "contribute"
    manage = "manage"
    
class ModuleName(str, Enum):

    category = "Category"
    product = "Product"
    dashboard = "Dashboard"
    finance = "Finance"
    sales = "Sales"
    presales = "Presales"
    trade_marketing = "Trade Marketing"
    visit = "Visit"
    order = "Order"
    route = "Route"
    territory = "Territory"
    point_of_sale = "Point Of Sale"
    address = "Address"
    users = "Users"
    role = "Role"
    organization = "Organization"
    inventory_management = "Inventory Management"
    route_schedule = "Route Schedule"
    penetration = "Penetration"
    administration = "Administration"

# class Module(SQLModel, table=True):
#     __tablename__ = "module"

#     id: int = Field(primary_key=True)
#     name: str
#     permissions: List["RoleModulePermission"] = Relationship(back_populates="module")


class RoleModulePermission(SQLModel, table=True):
    __tablename__ = "role_module_permission"

    id: int = Field(primary_key=True)
    role_id: int = Field(foreign_key="role.id")
    module: str 
    access_policy: Optional[AccessPolicy] = Field(default=AccessPolicy.deny)

    role: Optional[Role] = Relationship(back_populates="permissions")
    
class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    fullname: Optional[str] = Field(default=None, index=True)
    username: str = Field(unique=True, index=True)
    hashedPassword: str
    
    email: Optional[str] = Field(index=True)
    phone_number: Optional[str] = Field(default=None,index=True)
    organization_id: Optional[int] = Field(default=None, foreign_key="organization.id", index=True)
    role_id: Optional[int] = Field(default=None, foreign_key="role.id")
    scope: Scope = Field(default=Scope.personal_scope)
    scope_group_id: Optional[int] = Field(default=None, foreign_key="scope_group.id")
    gender: Optional[Gender]
    salary: Optional[float] = Field(default=None)
    position: Optional[str] = Field(default=None)    
    date_of_birth: Optional[datetime] = Field(default=None)
    date_of_joining: Optional[datetime] = Field(default=None)
    image: Optional[str] = Field(default=None)
    manager_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    id_type: Optional[IdType] = Field(default=None)
    id_number: Optional[str] = Field(default=None)    
    #address_id: Optional[int] = Field(default=None, foreign_key="address.id", index=True)



    
