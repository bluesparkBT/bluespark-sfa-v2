from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Territory(SQLModel, table=True):
    __tablename__ = "territory"

    id: Optional[int] = Field(default=None, primary_key=True)
    country: str = Field(index=True)  # Text type country
    name: str = Field(index=True)  # Territory name
    description: Optional[str] = Field(default=None)  # Territory description
    organization_id: int = Field(foreign_key="organization.id")  # Reference to Organization
    
    # Relationship with Route (One-to-Many)
    routes: List["Route"] = Relationship(back_populates="territory")


class Route(SQLModel, table=True):
    __tablename__ = "route"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # Route name
    description: Optional[str] = Field(default=None)  # Route description
    territory_id: int = Field(foreign_key="territory.id")  # Reference to Territory
    organization_id: int = Field(foreign_key="organization.id")  # Reference to Organization

    # Relationship with Territory
    territory: Optional[Territory] = Relationship(back_populates="routes")