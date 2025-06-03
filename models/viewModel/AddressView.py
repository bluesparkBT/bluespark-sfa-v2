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
    organization: Optional[int]
    

class GeolocationView(BaseModel):
    id: Optional[int] = None
    name: Annotated [ str, AfterValidator( validate_name) ]
    latitude: float
    longitude: Optional[float]
    address_id: Optional[int] = None
    organization: Optional[int]
