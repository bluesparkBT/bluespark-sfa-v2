from pydantic import model_validator
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, Self, List
from enum import Enum
from models.auth import ScopeGroup, ScopeGroupOrganizationLink


class Company(SQLModel, table=True): 
    __tablename__ = "company"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_name: str = Field(index=True)
    owner_name: Optional[str] = Field(default=None,index=True)
    description: Optional[str] = Field(default=None, index=True)
    sub_organization: Optional[List["Organization"]] = Relationship(back_populates="parent_company")

class OrganizationType(str, Enum):
    distributor = "Distributor"
    subagent = "SubAgent"
    retailer = "Retailer"
    company = "Company"

class Organization(SQLModel, table=True): 
    __tablename__ = "organization"

    id: Optional[int] = Field(default=None, primary_key=True)
    organization_name: str = Field(index=True)
    owner_name: Optional[str ]= Field(default=None, index=True)
    parent_company_id: Optional[int] = Field(default=None, foreign_key="company.id", index=True)
    parent_organization_id: Optional[int] = Field(default=None, foreign_key="organization.id", index=True)
    organization_type: OrganizationType = Field(default=OrganizationType.company)

    parent_company: Optional[Company] = Relationship(back_populates="sub_organization")
    scope_groups: List["ScopeGroup"] = Relationship(
        back_populates="organizations",
        link_model=ScopeGroupOrganizationLink
    )


    
    
