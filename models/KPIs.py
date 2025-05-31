from datetime import datetime
from enum import Enum
from pydantic import model_validator
from sqlmodel import SQLModel, Field
from typing import Optional, Self

from models.Dashboard import TimelineType


class Performance(SQLModel, table=True):
    __tablename__ = "performance"

    """
    Represents a performance record for an employee.

    This class is used to track the performance of an employee over a specific period. It includes
    details such as the employee's progress, the associated period, and flags to indicate if the
    record is active or has been modified.

    Attributes:
        id (Optional[integer]): The unique identifier of the performance record (primary key).
        employee (integer): The ID of the employee associated with the performance record.
        progress (float): The progress percentage of the performance (e.g., 0.75 for 75%).
        period (integer): The ID of the period associated with the performance record.
        dirty (Optional[string]): A flag indicating if the record has been modified. 
                               It can be `None`, "null", or an empty string.
        active (boolean): A flag indicating if the performance record is currently active.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    employee: int = Field(foreign_key="users.id", index=True)
    progress: float


class IndicatorType(str, Enum):
    """
    Represents the type of performance indicator.

    This enumeration defines the various types of performance indicators
    that can be used to measure employee or organizational performance.

    Members:
        none: No specific indicator type.
        SalesVolume: Measures sales volume performance.
        CallCompletion: Measures the completion rate of calls.
        Productivity: Measures productivity levels.
        Penetration: Measures market penetration or coverage.
    """

    none = None
    SalesVolume = "Sales Volume"
    CallCompletion = "Call Completion"
    Productivity = "Productivity"
    Penetration = "Penetration"


class Measurement(SQLModel, table=True):
    __tablename__ = "measurement"

    """
    Represents a measurement record for performance indicators.

    This class is used to store and manage data related to specific performance
    measurements, such as targets, actual values, and weights for different
    performance indicators.

    Attributes:
        id (Optional[integer]): The unique identifier of the measurement record (primary key).
        indicator_type (Optional[IndicatorType]): The type of performance indicator being measured.
        weight (float): The weight or importance of this measurement in overall performance.
        target (float): The target value for the measurement.
        actual (float): The actual value achieved for the measurement.
        performance (integer): The ID of the associated performance record.
        active (boolean): A flag indicating if the measurement record is currently active.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    indicator_type: Optional[IndicatorType] = Field(default=IndicatorType.none)
    weight: float
    target: float
    actual: float
    performance: int = Field(foreign_key="performance.id", index=True)

    @model_validator(mode="after")
    def check(self) -> Self:
        if self.indicator_type == "none" or self.indicator_type == "":
            self.indicator_type = None

        return self


class Period(SQLModel, table=True):
    __tablename__ = "period"

    """
    Represents a performance period in the system.

    This class is used to define and manage periods of time during which
    performance is measured. Each period has a name, type, start and end dates,
    and an active status.

    Attributes:
        id (Optional[integer]): The unique identifier of the period record (primary key).
        name (string): The name of the period (e.g., "Q1 2025").
        organization (Optional[int]): The ID of the organization associated with the period.
        type (string): The type of the period (e.g., "Quarterly", "Monthly").
        start (datetime): The start date and time of the period.
        end (datetime): The end date and time of the period.
        active (boolean): A flag indicating if the period is currently active.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    organization: Optional[int] = Field(foreign_key="organization.id", index=True)
    type: str
    start: datetime = Field(default=datetime.now(), index=True)
    end: datetime = Field(default=datetime.now(), index=True)
    timeline: TimelineType = Field(default=TimelineType.monthly)


class SalesVolumeTarget(SQLModel, table=True):
    __tablename__ = "sales_volume_target"

    """
    Represents a product target for performance tracking.

    This class is used to define and manage targets for specific products,
    including their weights, target values, and actual values achieved.

    Attributes:
        id (Optional[integer]): The unique identifier of the product target record (primary key).
        product (integer): The ID of the product associated with the target.
        weight (float): The weight or importance of this product target.
        target (float): The target value for the product.
        actual (float): The actual value achieved for the product.
        performance (integer): The ID of the associated performance record.
        active (boolean): A flag indicating if the product target record is currently active.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    product: int = Field(foreign_key="product.id", index=True)
    weight: float
    target: float
    actual: float
    performance: int = Field(foreign_key="performance.id", index=True)
    period: int = Field(foreign_key="period.id", index=True)


class CallCompletionTarget(SQLModel, table=True):
    __tablename__ = "call_completion_target"

    """
    Represents a completion target for performance tracking.

    This class is used to define and manage targets for route completions,
    including their weights, target values, and actual values achieved.

    Attributes:
        id (Optional[integer]): The unique identifier of the completion target record (primary key).
        route (integer): The ID of the route associated with the target.
        target (float): The target value for the route completion.
        weight (float): The weight or importance of this completion target.
        actual (float): The actual value achieved for the route completion.
        performance (integer): The ID of the associated performance record.
        active (boolean): A flag indicating if the completion target record is currently active.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    route: int = Field(foreign_key="route.id", index=True)
    target: float
    weight: float
    actual: float
    performance: int = Field(foreign_key="performance.id", index=True)
    period: int = Field(foreign_key="period.id", index=True)


class PenetrationTarget(SQLModel, table=True):
    __tablename__ = "penetration_target"

    """
    Represents a penetration target for performance tracking.

    This class is used to define and manage targets for market penetration
    within specific territories, including their weights, target values,
    and actual values achieved.

    Attributes:
        id (Optional[integer]): The unique identifier of the penetration target record (primary key).
        territory (integer): The ID of the territory associated with the target.
        target (float): The target value for market penetration.
        weight (float): The weight or importance of this penetration target.
        actual (float): The actual value achieved for market penetration.
        performance (integer): The ID of the associated performance record.
        active (boolean): A flag indicating if the penetration target record is currently active.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    territory: int = Field(foreign_key="territory.id", index=True)
    target: float
    weight: float
    actual: float
    performance: int = Field(foreign_key="performance.id", index=True)
    period: int = Field(foreign_key="period.id", index=True)


class ProductivityTarget(SQLModel, table=True):
    __tablename__ = "productivity_target"

    """
    Represents a productivity target for performance tracking.

    This class is used to define and manage targets for productivity
    within specific routes, including their weights, target values,
    and actual values achieved.

    Attributes:
        id (Optional[integer]): The unique identifier of the productivity target record (primary key).
        route (integer): The ID of the route associated with the target.
        target (float): The target value for productivity.
        weight (float): The weight or importance of this productivity target.
        actual (float): The actual value achieved for productivity.
        performance (integer): The ID of the associated performance record.
        active (boolean): A flag indicating if the productivity target record is currently active.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    route: int = Field(foreign_key="route.id", index=True)
    target: float
    weight: float
    actual: float
    performance: int = Field(foreign_key="performance.id", index=True)
    period: int = Field(foreign_key="period.id", index=True)