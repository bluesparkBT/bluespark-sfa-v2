from datetime import datetime
from enum import Enum
from sqlmodel import SQLModel


class TimelineType(str, Enum):
    daily = "Daily"
    weekly = "Weekly"
    monthly = "Monthly"
    yearly = "Yearly"


# Volume Related models
class Volume(SQLModel, table=False):
    period: str
    volume: float


class CashVSCredit(SQLModel, table=False):
    cashRatio: float
    creditRatio: float
    cashPercentage: float
    creditPercentage: float
    cash: float
    credit: float


class SalesVSTarget(SQLModel, table=False):
    sales: float
    target: float
    period: datetime


class YearToDate(SQLModel, table=False):
    period: str
    volume: float
    percentage: float


class OrderSales(SQLModel, table=False):
    order: float
    sales: float


class PresalesContribution(SQLModel, table=False):
    period: str
    presales: float
    presalesPercentage: float
    sales: float


class Filter(str, Enum):
    territory = "Territory"
    route = "Route"


class UnitOfPerformance(str, Enum):
    quantity = "Quantity"
    volume = "Volume"