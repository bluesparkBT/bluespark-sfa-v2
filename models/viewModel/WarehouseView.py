
from typing import Optional
from typing import Annotated
from pydantic import Field
from sqlmodel import SQLModel
from utils.util_functions import validate_name, validate_phone_number, validate_email
from pydantic import AfterValidator, BaseModel, ValidationError

class WarehouseGroup(BaseModel):
    id: Optional[int] = None
    name: str 
    access_policy: str

class Warehouse(BaseModel):
    id: Optional[int] = None
    warehouse_name: str 
    organization: int 
    address: Optional[int] = None
    landmark: Optional[str] = None
    latitude: float
    longitude: float

class Stock(BaseModel):
    id: Optional[int] = None
    warehouse: int 
    product: int 
    quantity: int 
    stock_type: str

class Vehicle(BaseModel):
    id: Optional[int] = None
    name: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] =None
    vin: Optional[str] = None
    description: Optional[str] = None
    plate_number: str 
    organization: int 

class WarehouseStop(BaseModel):
    id: Optional[int] = None
    request_type: str
    vehicle: Optional[int]= None
    product: int
    stock_type: str
    quantity: int 
