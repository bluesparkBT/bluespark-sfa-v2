from typing import Optional
from typing import Annotated
from pydantic import Field
from sqlmodel import SQLModel
from utils.util_functions import validate_name, capitalize_name
from pydantic import AfterValidator, BaseModel, ValidationError
from datetime import datetime
from models.RoutesAndVisits import SalesStatus, Visit_Data, VisitType, TravelStatus

class TravelCreate(BaseModel):
    employee: int
    route: list[int] | dict[int, str] | str
    date: Optional[datetime] 
    start_time: Optional[datetime] 
    start_location: Optional[int] = None
    finish_time: Optional[datetime] = None
    finish_location: Optional[int] = None
    sales_status: Optional[SalesStatus] = None
    visit_type: Optional[VisitType] = None
    point_of_sale: Optional[int] = None

class VisitDataCreate(BaseModel):
    date: Optional[datetime] 
    start_time: Optional[datetime] 
    end_time: Optional[datetime] 
    start_location: Optional[int] = None
    finish_location: Optional[int] = None
    travel_status: TravelStatus = TravelStatus.created

class VisitCreate(BaseModel):
    route_schedule: Optional[int] = None
    travel: int
    sales: Optional[int] = None
    point_of_sale: int
    visit_data: Optional[int] = None
    visit_type: VisitType