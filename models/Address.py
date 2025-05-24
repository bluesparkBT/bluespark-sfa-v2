from pydantic import model_validator
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, Self


class Address(SQLModel, table=True): 
    __tablename__ = "address"

    id: Optional[int] = Field(default=None, primary_key=True)
    country: str = Field(default="Ethiopia", index=True)
    city: str = Field(index=True)
    sub_city: str = Field(index=True)
    woreda: str = Field(index=True)
    geolocation: Optional["Geolocation"] = Relationship(back_populates="address")


    @model_validator(mode="after")
    def check(self) -> Self:
        if self.landmark == "null" or self.landmark == "":
            self.landmark = None
        return self


class Geolocation(SQLModel, table=True):
    __tablename__ = "geolocation"


    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(default=None)
    address_id: Optional[int] = Field(default=None, foreign_key="address.id", index=True)
    latitude: float
    longitude: float

    address: Optional[Address] = Relationship(back_populates="geolocation")
   

    @model_validator(mode="after")
    def check(self) -> Self:
        if self.name == "null" or self.name == "":
            self.name = None
        if self.address == "null" or self.address == "":
            self.address = None
        return self
