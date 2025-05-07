from typing import Optional, Self, List
from pydantic import model_validator, BaseModel, Base64Bytes
from sqlmodel import Relationship

from models.MultiTenant import Company

class Organization(BaseModel): 

    id: int
    organization_name: str
    owner_name: Optional[str]
    organization_type: str | dict[int, str] | int | None
    parent_company_id: int | None = None
    parent_organization_id: int | None = None
    parent_company: Optional["Company"] = Relationship(back_populates="sub_organization")

    
class TenantCreation(BaseModel): 

    id: int
    company_name: str
    owner_name: str
    description: str
    logo_image: str | Base64Bytes | None = None

    @model_validator(mode="after")
    def check(self) -> Self:
        if self.description == "null" or self.description == "":
            self.description = None

        if self.parent_organization == "null" or self.parent_organization == "":
            self.parent_organization = None
        return self