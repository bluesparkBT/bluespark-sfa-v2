from datetime import datetime
from enum import Enum
from pydantic import model_validator
from sqlmodel import SQLModel, Field
from typing import Optional, Self

class Territory(SQLModel, table=True):
    __tablename__ = "territory"

    """
    Represents a territory.

    Attributes:
        id (Optional[int]): Unique identifier of the territory (primary key).
        city (str): City of the territory.
        name (str): Name of the territory (indexed).
        description (Optional[str]): Description of the territory.
        organization (Optional[int]): ID of the organization this territory belongs to (foreign key to organization.id).
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    country: str = Field(default="Ethiopia", index=True)
    description: Optional[str] = Field(default=None)
    organization: Optional[int] = Field(default=None, foreign_key="organization.id", ondelete="CASCADE")



class Route(SQLModel, table=True):
    __tablename__ = "route"

    """
    Represents a delivery or sales route in the system.

    This class is used to define and manage routes assigned to employees or sales representatives.
    A route typically consists of a series of points of sale or locations that need to be visited
    within a specific territory.

    Attributes:
        id (Optional[integer]): The unique identifier of the route (primary key).
        name (string): The name of the route (e.g., "Downtown Route").
        description (Optional[string]): A detailed description of the route, such as its purpose or coverage area.
        territory (integer): The ID of the territory associated with the route.
        active (boolean): A flag indicating whether the route is currently active.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    territory: int = Field(foreign_key="territory.id", index=True, ondelete = "CASCADE")
    description: Optional[str] = Field(default=None)
    organization: Optional[int] = Field(default=None, foreign_key="organization.id", ondelete="CASCADE")



class RoutePoint(SQLModel, table=True):
    __tablename__ = "route_point"

    """
    Represents a specific point of sale or location on a route.

    This class is used to associate points of sale with routes, enabling the system to track
    which locations are part of a given route. It also includes information about the territory
    and organization associated with the route point.

    Attributes:
        id (Optional[integer]): The unique identifier of the route point (primary key).
        point_of_sale (integer): The ID of the point of sale associated with this route point.
        route (integer): The ID of the route to which this point belongs.
        territory (Optional[integer]): The ID of the territory associated with this route point.
        organization (Optional[integer]): The ID of the organization associated with this route point.
        active (boolean): A flag indicating whether the route point is currently active.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    point_of_sale: int = Field(foreign_key="point_of_sale.id", index=True)
    route: int = Field(foreign_key="route.id", index=True)
    territory: Optional[int] = Field(
        default=None, foreign_key="territory.id", index=True
    )


class RouteSchedule(SQLModel, table=True):
    __tablename__ = "route_schedule"

    """
    Represents a scheduled route for an employee.

    This class is used to manage the scheduling of routes for employees, including the date
    of the schedule, the employee assigned to the route, and any additional remarks.

    Attributes:
        id (Optional[integer]): The unique identifier of the route schedule (primary key).
        date (datetime): The date on which the route is scheduled.
        employee (integer): The ID of the employee assigned to the route.
        route (integer): The ID of the route being scheduled.
        remark (Optional[string]): Additional remarks or notes about the schedule.
        active (boolean): A flag indicating whether the schedule is currently active.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime = Field(default=datetime.now(), index=True)
    employee: int = Field(foreign_key="users.id", index=True)
    route: int = Field(foreign_key="route.id", index=True)
    remark: Optional[str] = Field(default=None)


class TravelStatus(str, Enum):
    """
    Represents the status of a travel or journey.

    This enumeration is used to track the progress of a travel, such as whether it has been
    created, started, finished, or cancelled.

    Members:
        created: Indicates that the travel has been created but not yet started.
        started: Indicates that the travel has started.
        finished: Indicates that the travel has been completed.
        cancelled: Indicates that the travel has been cancelled.
    """

    # only used in the frontend to check whether it needs to be updated or not
    created = "Created"
    started = "Started"
    finished = "Finished"
    cancelled = "Cancelled"

class SalesStatus(str, Enum):
    """
    Represents the status of a sale made during a visit.

    This enumeration is used to track whether a sale was made, if it was cancelled, or if it was not applicable.

    Members:
        sale: Indicates that a sale was made.
        cancelled: Indicates that the sale was cancelled.
        not_applicable: Indicates that the sale is not applicable (e.g., no sale made).
    """

    sale = "Sale"
    not_sale = "No Sale"
    cancelled = "Cancelled"
    
class VisitType(str, Enum):
    """
    Represents the type of visit made by an employee.

    This enumeration is used to categorize visits based on their purpose or nature,
    such as whether they are planned or unplanned visits.

    Members:
        sales: Indicates a sales-related visit.
        customerService: Indicates a customer service-related visit.
        other: Indicates any other type of visit.
    """

    planned_visit = "Planned Visit"
    unplanned_visit = "Unplanned Visit"
    other = "Other"
    
class Travel(SQLModel, table=True):
    __tablename__ = "travel"

    """
    Represents a travel record for an employee.

    This class is used to track the details of a travel, including the route taken, the start
    and finish times, and the locations involved. It is useful for monitoring employee movements
    and ensuring that routes are completed as planned.

    Attributes:
        id (Optional[integer]): The unique identifier of the travel record (primary key).
        employee (integer): The ID of the employee undertaking the travel.
        route (integer): The ID of the route being traveled.
        date (datetime): The date of the travel.
        start_time (datetime): The start time of the travel.
        start_location (Optional[integer]): The ID of the starting location.
        finish_time (Optional[datetime]): The finish time of the travel.

        finish_location (Optional[integer]): The ID of the finishing location.
        active (bool): A flag indicating whether the travel record is currently active.

    """

    id: Optional[int] = Field(default=None, primary_key=True)
    employee: int = Field(foreign_key="users.id", index=True)
    route: int = Field(foreign_key="route.id", index=True)
    date: datetime = Field(default=datetime.now(), index=True)
    start_time: datetime = Field(default=datetime.now(), index=True)
    start_location: Optional[int] = Field(
        default=None, foreign_key="geolocation.id", index=True
    )
    finish_time: Optional[datetime] = Field(default=datetime.now(), index=True)
    finish_location: Optional[int] = Field(
        default=None, foreign_key="geolocation.id", index=True
    )
    sales_status: Optional[SalesStatus] = Field(default=None)
    visit_type: Optional[VisitType] = Field(default=None)
    point_of_sale: Optional[int] = Field(
        default=None, foreign_key="point_of_sale.id", index=True)



class Visit_Data(SQLModel, table=True):
    __tablename__ = "visit_data"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime = Field(default=datetime.now(), index=True)
    start_time: datetime = Field(default=datetime.now(), index=True)
    end_time: datetime = Field(default=datetime.now(), index=True)
    start_location: Optional[int] = Field(
        default=None, foreign_key="geolocation.id", index=True)
    finish_location: Optional[int] = Field(
        default=None, foreign_key="geolocation.id", index=True)
    travel_status: TravelStatus = Field(default=TravelStatus.created)


class Visit(SQLModel, table=True):
    __tablename__ = "visit"

    """
    Represents a visit to a point of sale during a travel.

    This class is used to track visits made by employees to specific points of sale. It includes
    details such as the time of the visit, the location, and any remarks if no sale was made.

    Attributes:
        id (Optional[integer]): The unique identifier of the visit record (primary key).
        location (Optional[integer]): The ID of the location where the visit occurred.
        reference_location (Optional[integer]): The ID of the reference location for the visit.
        travel (integer): The ID of the travel associated with the visit.
        time (datetime): The time at which the visit occurred.
        sales (Optional[integer]): The ID of the sale made during the visit, if any.
        point_of_sale (integer): The ID of the point of sale visited.
        no_sale_remark (Optional[string]): A remark explaining why no sale was made, if applicable.
        active (bool): A flag indicating whether the visit record is currently active.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    route_schedule: Optional[int] = Field(
        default=None, foreign_key="route_schedule.id", index=True)
    travel: int = Field(foreign_key="travel.id", index=True)
    sales: Optional[int] = Field(default=None, foreign_key="sale.id", index=True)
    point_of_sale: int = Field(foreign_key="point_of_sale.id", index=True)
    visit_data: Optional[int] = Field(default=None, foreign_key="visit_data.id")
    visit_type: VisitType = Field(default=None)


class RequestType(str, Enum):
    """
    Enum representing the type of request for inventory.

    Attributes:

    """
    Return = "Return"
    Pickup = "Pickup"
    Defect_return = "Defect Return"


class RequestStatus(str, Enum):
    """
    Enum representing the status of a request.

    Attributes:
        Pending (str): The request is pending approval.
        Approved (str): The request has been approved.
        Rejected (str): The request has been rejected.
    """

    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"
