from typing import Optional
from typing import Annotated
from pydantic import Field
from sqlmodel import SQLModel
from utils.util_functions import validate_name, capitalize_name
from pydantic import AfterValidator, BaseModel, ValidationError
from datetime import datetime


class RouteCreate(BaseModel):
    name: str
    description: Optional[Annotated [ str,  AfterValidator( validate_name) ] ] = None
    territory: Optional[str] | dict[int, str] | int
    organization: Optional[int] = None

class RoutePointCreate(BaseModel):
    point_of_sale: int
    route: int
    territory: Optional[int] = None
    organization: Optional[int] = None

class RouteScheduleCreate(BaseModel):
    date: datetime
    employee: int
    route: int
    remark: Optional[Annotated [ str,  AfterValidator( validate_name) ] ] = None