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
    organization: Optional[int] = Field(default=None, foreign_key="organization.id", ondelete="CASCADE", index=True)


class Geolocation(SQLModel, table=True):
    __tablename__ = "geolocation"


    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(default=None)
    latitude: float
    longitude: float
    address_id: Optional[int] = Field(default=None, foreign_key="address.id", index=True)
    organization: Optional[int] = Field(default=None, foreign_key="organization.id", ondelete="CASCADE", index=True)

