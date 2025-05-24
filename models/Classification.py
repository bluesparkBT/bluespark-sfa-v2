from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import date



class ClassificationGroup(SQLModel, table=True):
    __tablename__ = "classification_group"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str
    # organizations: list["Organization"] = Relationship(back_populates="organization")#  Reference to Organization

    # Optional references
    # point_of_sale_id: Optional[int] = Field(default=None, foreign_key="point_of_sale.id")
    territory_id: Optional[int] = Field(default=None, foreign_key="territory.id")
    route_id: Optional[int] = Field(default=None, foreign_key="route.id")

    # Relationship with CustomerDiscount
    customer_discounts: list["CustomerDiscount"] = Relationship(back_populates="classification_group")


class CustomerDiscount(SQLModel, table=True):
    __tablename__ = "customer_discount"

    id: Optional[int] = Field(default=None, primary_key=True)
    start_date: date = Field(default=None)    
    end_date: date = Field(default=None)
    discount: float
    image: Optional[str] = Field(default=None)  # File storage for an image
    
    classification_group_id: int = Field(foreign_key="classification_group.id")  # Reference to ClassificationGroup
    classification_group: Optional[ClassificationGroup] = Relationship(back_populates="customer_discounts")