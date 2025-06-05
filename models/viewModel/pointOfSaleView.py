from pydantic import BaseModel, AfterValidator
from typing import Optional, Annotated
from enum import Enum
from utils.util_functions import validate_name, validate_email

class POSStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"

def validate_status(value: str) -> str:
    if value not in POSStatus.__members__.values():
        raise ValueError("Invalid status: Must be 'Active' or 'Inactive'.")
    return value

class PointOfSaleView(BaseModel):
    
    status: Annotated[POSStatus, AfterValidator(validate_status)]
    registered_on: str
    organization: int
    outlet_id: Optional[int]
    walk_in_customer_id: Optional[int]

class UpdatePointOfSaleView(BaseModel):
    id: Optional[int]
    status: Annotated[POSStatus, AfterValidator(validate_status)]
    registered_on: str
    organization: int
    outlet_id: Optional[int]
    walk_in_customer_id: Optional[int]


class OutletView(BaseModel):

    name: Annotated[str, AfterValidator(validate_name)]
    channel: str
    tin: str
    phone: str
    email: str
    location_id: int

class UpdateOutletView(BaseModel):
    id: Optional[int]
    name: Annotated[str, AfterValidator(validate_name)]
    channel: str
    tin: str
    phone: str
    email: str
    location_id: int   

class WalkInCustomerView(BaseModel):
    name: Annotated[str, AfterValidator(validate_name)]
    email: Annotated[Optional[str], AfterValidator(validate_email)]
    location_id: Optional[int]
    route_id: Optional[int]
    territoy_id: Optional[int]

class UpdateWalkInCustomerView(BaseModel):
    id: Optional[int]
    name: Annotated[str, AfterValidator(validate_name)]
    email: Annotated[Optional[str], AfterValidator(validate_email)]
    location_id: Optional[int]
    route_id: Optional[int]
    territoy_id: Optional[int]

