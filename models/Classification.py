from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import date
from models.Account import Organization

class ClassificationGroup(SQLModel, table=True):
    __tablename__ = "classification_group"

    id: Optional[int] = Field(default=None, primary_key=True)
    # For example: "Gold", "Silver", "Platinum"
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    # organization_id: int = Field(foreign_key="organization.id")  # Reference to Organization
    organization: Optional[Organization] = Relationship(back_populates="classification_groups")


    point_of_sale_id: Optional[int] = Field(default=None, foreign_key="point_of_sale.id")
    territory_id: Optional[int] = Field(default=None, foreign_key="territory.id")
    route_id: Optional[int] = Field(default=None, foreign_key="route.id")

    # A classification group can have many discount entries.
    customer_discounts: List["CustomerDiscount"] = Relationship(back_populates="classification_group")


class CustomerDiscount(SQLModel, table=True):
    __tablename__ = "customer_discount"

    id: Optional[int] = Field(default=None, primary_key=True)
    # Defines the validity period for the discount
    start_date: date = Field()
    end_date: date = Field()
    # The discount amount or percentage applied to customers of the classification.
    discount: float = Field(description="Discount amount or percentage applicable.")

    # Each discount references the classification group to which it applies.
    classification_group_id: int = Field(foreign_key="classification_group.id")
    classification_group: Optional[ClassificationGroup] = Relationship(back_populates="customer_discounts")