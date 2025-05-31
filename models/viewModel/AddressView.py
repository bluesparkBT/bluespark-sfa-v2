from typing import Optional
from typing import Annotated
from pydantic import Field
from sqlmodel import SQLModel
from utils.util_functions import validate_name, capitalize_name
from pydantic import AfterValidator, BaseModel, validator


class AddressView(BaseModel):
    id: Optional[int] = None
    country: Optional[str] = Field(default="Ethiopia", max_length=100)
    city: str 
    sub_city: str 
    woreda: str 

    @validator("city", "sub_city", "woreda")
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    


class GeolocationView(BaseModel):
    id: Optional[int] = None
    name: Annotated [ str, AfterValidator( validate_name) ]
    latitude: float
    longitude: float
    address_id: Optional[int] = None

    @validator("latitude", "longitude")
    def must_be_valid_float(cls, v):
        if v is None:
            raise ValueError("Latitude and longitude are required")
        return v

