from enum import Enum
from pydantic import model_validator
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, Self, List


class Address(SQLModel, table=True):  # defined in Employee in ASP
    __tablename__ = "address"

    """
    SQLModel class representing an address.

    Attributes:
        id: Optional[int] - The unique identifier of the address (primary key).
        city: str - The city of the address.
        sub_city: str - The sub-city or district of the address.
        landmark: Optional[str] - A notable landmark near the address.
        locations: List[Location] - A list of locations associated with this address (backpopulated).
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    country: str = Field(default="Ethiopia", index=True)
    city: str = Field(index=True)
    sub_city: str = Field(index=True)
    woreda: str = Field(index=True)
    landmark: Optional[str] = Field(default=None, index=True)
    locations: List["Location"] = Relationship(back_populates="address")


    @model_validator(mode="after")
    def check(self) -> Self:
        if self.landmark == "null" or self.landmark == "":
            self.landmark = None
        return self


class Location(SQLModel, table=True):
    __tablename__ = "location"

    """
    SQLModel class representing a location.

    Attributes:
        id: Optional[int] - The unique identifier of the location (primary key).
        name: Optional[str] - The name of the location (default: None).
        address: Optional[int] - The foreign key referencing the address.
        latitude: float - The latitude coordinate of the location.
        longitude: float - The longitude coordinate of the location.
        address_rel: Optional[Address] - The associated Address object (back reference).
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(default=None)
    address_id: Optional[int] = Field(default=None, foreign_key="address.id", index=True)
    latitude: float
    longitude: float
    address: Optional[Address] = Relationship(back_populates="locations")

    @model_validator(mode="after")
    def check(self) -> Self:
        if self.name == "null" or self.name == "":
            self.name = None
        if self.address == "null" or self.address == "":
            self.address = None
        return self
