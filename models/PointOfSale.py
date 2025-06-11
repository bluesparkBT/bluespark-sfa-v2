from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
from models.Product_Category import PointOfSaleLink,InheritanceGroup
from datetime import datetime
# Define Enum for status
class POSStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class ChannelType(str, Enum):
    SUQ = "Suq"
    MINI_MARKET = "MiniMarket"
    SUPERMARKET = "Supermarket"
    HOTEL = "Hotel"
    WHOLESALE = "Wholesale"
    FRUIT_HOUSE = "FruitHouse"
    BURGER_HOUSE_PIZZERIA = "BurgerHousePizzeria"
    CAFE_RESTAURANT = "CafeRestaurant"
    PHARMACY = "Pharmacy"
    
class PointOfSale(SQLModel, table=True):
    __tablename__ = "point_of_sale"

    id: Optional[int] = Field(default=None, primary_key=True)
    status: POSStatus  # Enum status
    registered_on: datetime  # Registration date in text format
    # default_credit_group_id: int = Field(foreign_key="credit_group.id")  # Reference to Default Credit Group
    organization: int = Field(foreign_key="organization.id", ondelete="CASCADE")  # Reference to Organization

    # Optional references
    outlet_id: Optional[int] = Field(default=None, foreign_key="outlet.id", ondelete = "CASCADE")  # Reference to Outlet
    walk_in_customer_id: Optional[int] = Field(default=None, foreign_key="walk_in_customer.id" ,ondelete="CASCADE")

    # Relationships
    outlet: Optional["Outlet"] = Relationship(back_populates="point_of_sale")
    walk_in_customer: Optional["WalkInCustomer"] = Relationship(back_populates="point_of_sale")
    inheritance_groups: List["InheritanceGroup"] = Relationship(back_populates="point_of_sales", link_model=PointOfSaleLink)

class Outlet(SQLModel, table=True):
    __tablename__ = "outlet"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # Outlet name
    channel: Optional [ChannelType]  # Enum channel (assuming it's a predefined list)
    tin: Optional [str]  # Tax Identification Number
    phone: Optional [str]  # Phone number
    email: Optional [str] = Field(index=True)  # Email address
    location_id: int = Field(foreign_key="geolocation.id", ondelete="CASCADE")  # Reference to geolocation

    # Relationship with PointOfSale
    point_of_sale: Optional[PointOfSale] = Relationship(back_populates="outlet")


class WalkInCustomer(SQLModel, table=True):
    __tablename__ = "walk_in_customer"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # Walk-in customer name
    email: Optional[str] = Field(default=None)  # Optional email (Alphanumeric type assumed as text)
    route_id: Optional[int] = Field(default=None, foreign_key="route.id", ondelete="CASCADE")
    territoy_id: Optional[int] = Field(default=None, foreign_key="territory.id" , ondelete="CASCADE")  # Optional Reference to Location
  # Optional Reference to Location
    # Relationship with PointOfSale
    point_of_sale: Optional[PointOfSale] = Relationship(back_populates="walk_in_customer")
