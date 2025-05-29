from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from models.KPIs import IndicatorType
from typing import Annotated
from pydantic import AfterValidator
from utils.util_functions import validate_name, capitalize_name
from models.Dashboard import TimelineType

class  MeasurementCreation(BaseModel):
    indicator_type: Optional[IndicatorType]
    weight: float | int
    target: float | int
    actual: float | int
    performance: int

class PerformanceCreation(BaseModel):
    employee: int
    progress: float | int

class period(BaseModel):
    name: Annotated [ str, AfterValidator( validate_name) ]
    organization_id: Optional[int]
    type: str
    start: datetime
    end: datetime
    timeline: TimelineType
    
class SalesVolumeTargetCreation(BaseModel):
    product: int
    weight: float | int
    target: float | int
    actual: float | int
    performance: int
    period: int

class CallCompletionTargetCreation(BaseModel):
    route: list[int] | dict[int, str] | str
    weight: float | int
    target: float | int
    actual: float | int
    performance: int
    period: int

class PenetrationTargetCreation(BaseModel):
    territory: Optional[str] | dict[int, str] | int
    weight: float | int
    target: float | int
    actual: float | int
    performance: int
    period: int

class ProductivityTargetCreation(BaseModel):
    route: list[int] | dict[int, str] | str
    weight: float | int
    target: float | int
    actual: float | int
    performance: int
    period: int