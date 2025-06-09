from pydantic import BaseModel, AfterValidator
from typing import Optional, Annotated
from enum import Enum
from utils.util_functions import validate_name, validate_email,validate_phone_number
from pydantic import validator


class PointOfSaleView(BaseModel):
    
    outlet_name: Optional [Annotated[str, AfterValidator(validate_name)]]
    # outlet_id: Optional[int]
    channel:Optional [int]
    tin: Optional [str]
    phone: Optional [str]
    outlet_email: Optional [str]
    latitude: float
    longitude: float
    
    # customer_id: Optional [int]
    customer_name: Optional [Annotated[str, AfterValidator(validate_name)]]
    customer_email: Optional[Annotated[str, AfterValidator(validate_name)]]
    route: Optional[int]
    territoy: Optional[int]

class UpdatePointOfSaleView(BaseModel):
    id: Optional[int]
    outlet_name: Optional [Annotated[str, AfterValidator(validate_name)]]
    # outlet_id: Optional[int]
    channel:Optional [int]
    tin: Optional [str]
    phone: Optional [str]
    outlet_email: Optional [str]
    latitude: float
    longitude: float
    
    # customer_id: Optional [int]
    customer_name: Optional [Annotated[str, AfterValidator(validate_name)]]
    customer_email: Optional[Annotated[str, AfterValidator(validate_name)]]
    route: Optional[int]
    territoy: Optional[int]

class OutletView(BaseModel):
    id: Optional [int | str]
    outlet_name: Optional [Annotated[str, AfterValidator(validate_name)]]
    # outlet_id: Optional[int]
    channel:Optional [int]
    tin: Optional [str]
    phone: Optional [str]
    outlet_email: Optional [str]
    latitude: float
    longitude: float


class UpdateOutletView(BaseModel):
    id: Optional[int|str]
    outlet_name: Optional [Annotated[str, AfterValidator(validate_name)]]
    # outlet_id: Optional[int]
    channel:Optional [int]
    tin: Optional [str]
    phone: Optional [str]
    outlet_email: Optional [str]
    latitude: float
    longitude: float

class WalkInCustomerView(BaseModel):

    customer_name: Optional [Annotated[str, AfterValidator(validate_name)]]
    customer_email: Optional[Annotated[str, AfterValidator(validate_name)]]
    route: Optional[int]
    territoy: Optional[int]

class UpdateWalkInCustomerView(BaseModel):
    id: Optional[int|str]
    customer_name: Optional [Annotated[str, AfterValidator(validate_name)]]
    customer_email: Optional[Annotated[str, AfterValidator(validate_name)]]
    route: Optional[int]
    territoy: Optional[int]

    # @validator("latitude", "longitude", pre=True)
    # def empty_str_to_none(cls, v):
    #     if v == "":
    #         return None
    #     return v
# def validate_status(value: str) -> str:
#     if value not in POSStatus.__members__.values():
#         raise ValueError("Invalid status: Must be 'Active' or 'Inactive'.")
#     return value


