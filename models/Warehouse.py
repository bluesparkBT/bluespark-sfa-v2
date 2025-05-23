from sqlmodel import SQLModel, Field, Relationship
from enum import Enum   
from typing import Optional, List
from datetime import  datetime


class RequestType(str, Enum):
   stock_out = "Stock Out"
   transfer = "Transfer"
   return_defect = "Return Defect"
   return_normal = "Return Normal"

class LogType(str, Enum):
   stock_in = "Stock In"
   stock_out = "Stock Out"
   transfer = "Transfer"
   return_defect = "Return Defect"
   return_normal = "Return Normal"

class StockType(str, Enum):
   regular = "Regular"
   promotional = "Promotional"

class RequestStatus(str, Enum):
   pending = "Pending"
   approved = "Approved"
   rejected = "Rejected"


class WarehouseStoreAdminLink(SQLModel, table=True):
    __tablename__ = "warehouse_store_admin_link"

    id: Optional[int] = Field(default=None, primary_key=True)
    warehouse_id: int = Field(foreign_key="warehouse.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)

class Warehouse(SQLModel, table=True):
    __tablename__ = "warehouse"

    id: Optional[int] = Field(default=None, primary_key=True)
    warehouse_name: str = Field(index=True)
    organization_id: int = Field(foreign_key="organization.id")
    location_id: int = Field(foreign_key="geolocation.id")
    store_admins: List["User"] = Relationship(back_populates="warehouses", link_model=WarehouseStoreAdminLink)
    stocks: Optional[List["Stock"]] = Relationship(back_populates="warehouse")
    organization: Optional["Organization"] = Relationship(back_populates="warehouses")


class Stock(SQLModel, table=True):
    __tablename__ = "stock"

    id: Optional[int] = Field(default=None, primary_key=True)
    warehouse_id: int = Field(foreign_key="warehouse.id")
    product_id: int = Field(foreign_key="product.id")
    category_id: int = Field(foreign_key="category.id")
    subcategory_id: Optional[int] = Field(foreign_key="category.id", default=None)
    quantity: int = Field(default=1)
    date_added: Optional[datetime] = Field(default=None)
    stock_type: StockType = Field(default=StockType.regular)
    warehouse: Optional[Warehouse] = Relationship(back_populates="stocks")
    product: Optional["Product"] = Relationship(back_populates="stocks")
    category: Optional["Category"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Stock.category_id]"},
        back_populates="category_stocks"
    )
    subcategory: Optional["Category"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Stock.subcategory_id]"},
        back_populates="subcategory_stocks"
    )
    stock_logs: Optional[List["StockLog"]] = Relationship(back_populates="stock")
    warehouse_stops: Optional[List["WarehouseStop"]] = Relationship(back_populates="stock")


class StockLog(SQLModel, table=True):
    __tablename__ = "stock_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    stock_id: int = Field(foreign_key="stock.id")
    stock_in_date: Optional[datetime] = Field(default=None)
    stock_out_date: Optional[datetime] = Field(default=None)
    request_type: Optional[RequestType] = Field(default=None)
    log_type: LogType = Field(default=LogType.stock_in)
    stock: Optional["Stock"] = Relationship(back_populates="stock_logs")

class Vehicle(SQLModel, table=True):
    __tablename__ = "vehicle"
    id: int = Field(primary_key=True)
    name: str
    make: Optional[str] = Field(index=True) 
    model: Optional[str] = Field(index=True)
    year: Optional[int] = Field(default=None)
    color: Optional[str] = Field(default=None)
    vin: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    plate_number: str = Field(index=True)
    organization_id: Optional[int] = Field(foreign_key="organization.id", index=True)
    warehouse_stops: Optional[List["WarehouseStop"]] = Relationship(back_populates="vehicle")

class WarehouseStop(SQLModel, table=True):
    __tablename__ = "warehouse_stop"

    id: Optional[int] = Field(default=None, primary_key=True)
    requester_id: int = Field(foreign_key="users.id")
    request_type: RequestType = Field(default=RequestType.stock_out)
    request_status: RequestStatus = Field(default=RequestStatus.pending)
    request_date: Optional[datetime] = Field(default=None)
    approver_id: Optional[int] = Field(foreign_key="users.id", default=None)
    approve_date: Optional[datetime] = Field(default=None)
    confirmed: Optional[bool] = Field(default=False)
    confirm_date: Optional[datetime] = Field(default=None)
    vehicle_id: Optional[int]= Field(foreign_key="vehicle.id")
    stock_id: Optional[int]= Field(foreign_key="stock.id")
    stock_type: StockType = Field(default=StockType.regular)
    quantity: int = Field(default=1)
    vehicle: Optional["Vehicle"] = Relationship(back_populates="warehouse_stops")
    requester: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[WarehouseStop.requester_id]"},
        back_populates="requester_warehouse_stops"
    )
    approver: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[WarehouseStop.approver_id]"},
        back_populates="approver_warehouse_stops"
    )
    stock: Optional["Stock"] = Relationship(back_populates="warehouse_stops")




    





