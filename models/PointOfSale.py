from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum

# Define Enum for status
class POSStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"

class PointOfSale(SQLModel, table=True):
    __tablename__ = "point_of_sale"

    id: Optional[int] = Field(default=None, primary_key=True)
    status: POSStatus  # Enum status
    registered_on: str = Field(index=True)  # Registration date in text format
    organization_id: int = Field(foreign_key="organization.id")  # Reference to Organization
    # default_credit_group_id: int = Field(foreign_key="credit_group.id")  # Reference to Default Credit Group

    # Optional references
    outlet_id: Optional[int] = Field(default=None, foreign_key="outlet.id")
    walk_in_customer_id: Optional[int] = Field(default=None, foreign_key="walk_in_customer.id")

    # Relationships
    outlet: Optional["Outlet"] = Relationship(back_populates="point_of_sale")
    walk_in_customer: Optional["WalkInCustomer"] = Relationship(back_populates="point_of_sale")


class Outlet(SQLModel, table=True):
    __tablename__ = "outlet"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # Outlet name
    channel: str  # Enum channel (assuming it's a predefined list)
    tin: str  # Tax Identification Number
    phone: str  # Phone number
    email: str = Field(index=True)  # Email address
    location_id: int = Field(foreign_key="location.id")  # Reference to Location

    # Relationship with PointOfSale
    point_of_sale: Optional[PointOfSale] = Relationship(back_populates="outlet")


class WalkInCustomer(SQLModel, table=True):
    __tablename__ = "walk_in_customer"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # Walk-in customer name
    email: Optional[str] = Field(default=None)  # Optional email (Alphanumeric type assumed as text)
    landmark: str = Field(index=True)  # Landmark for customer reference
    location_id: Optional[int] = Field(default=None, foreign_key="location.id")  # Optional Reference to Location

    # Relationship with PointOfSale
    point_of_sale: Optional[PointOfSale] = Relationship(back_populates="walk_in_customer")