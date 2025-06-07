from sqlmodel import SQLModel, Field, Relationship
from enum import Enum   
from typing import Optional, List
from datetime import  datetime

class AccessPolicy(str, Enum):
    deny = "deny"
    view = "view"
    edit = "edit"
    contribute = "contribute"
    manage = "manage"


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

class WarehouseGroupLink(SQLModel, table=True):
    __tablename__ = "warehouse_group_link"

    id: Optional[int] = Field(default=None, primary_key=True)
    warehouse_id: int = Field(foreign_key="warehouse.id", index=True)
    warehouse_group_id: int = Field(foreign_key="warehouse_group.id", index=True)



class WarehouseStoreAdminLink(SQLModel, table=True):
    __tablename__ = "warehouse_store_admin_link"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    warehouse_group_id: int = Field(foreign_key="warehouse_group.id", index=True), 
    
class WarehouseGroup(SQLModel, table=True):
    __tablename__ = "warehouse_group"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    access_policy: AccessPolicy
    organization_id: int = Field(foreign_key="organization.id", ondelete="CASCADE")
    warehouses: Optional[List["Warehouse"]] = Relationship(back_populates="warehouse_groups", link_model=WarehouseGroupLink)
    store_admins: Optional[List["User"]] = Relationship(back_populates="warehouse_groups", link_model=WarehouseStoreAdminLink)

class Warehouse(SQLModel, table=True):
    __tablename__ = "warehouse"

    id: Optional[int] = Field(default=None, primary_key=True)
    warehouse_name: str = Field(index=True)
    organization_id: int = Field(foreign_key="organization.id", ondelete="CASCADE")
    address_id: Optional[int] = Field(foreign_key="address.id", default=None)
    landmark: Optional[str] = Field(default=None) 
    location_id: int = Field(foreign_key="geolocation.id")
    warehouse_groups: List["WarehouseGroup"] = Relationship(back_populates="warehouses", link_model=WarehouseGroupLink)
    stocks: Optional[List["Stock"]] = Relationship(back_populates="warehouse")
    stock_logs: Optional[List["StockLog"]] = Relationship(back_populates="warehouse")
    warehouse_stops: Optional[List["WarehouseStop"]] = Relationship(back_populates="warehouse")
    # organization: Optional["Organization"] = Relationship(back_populates="warehouses")


class Stock(SQLModel, table=True):
    __tablename__ = "stock"

    id: Optional[int] = Field(default=None, primary_key=True)
    warehouse_id: int = Field(foreign_key="warehouse.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int = Field(default=1)
    date_added: datetime 
    stock_type: StockType = Field(default=StockType.regular)
    warehouse: Optional[Warehouse] = Relationship(back_populates="stocks")
    product: Optional["Product"] = Relationship(back_populates="stock")


class StockLog(SQLModel, table=True):
    __tablename__ = "stock_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    stock_id: str = Field(index=True)
    warehouse_id: int = Field(foreign_key="warehouse.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int = Field(default=1)
    stock_in_date: Optional[datetime] = Field(default=None)
    stock_out_date: Optional[datetime] = Field(default=None)
    request_type: Optional[RequestType] = Field(default=None)
    log_type: LogType = Field(default=LogType.stock_in)
    stock_type: StockType = Field(default=StockType.regular)
    warehouse: Optional[Warehouse] = Relationship(back_populates="stock_logs")
    product: Optional["Product"] = Relationship(back_populates="stock_log")

class Vehicle(SQLModel, table=True):
    __tablename__ = "vehicle"
    id: int = Field(primary_key=True)
    name: str
    make: Optional[str] = Field(index=True, default=None) 
    model: Optional[str] = Field(index=True, default=None)
    year: Optional[int] = Field(default=None)
    color: Optional[str] = Field(default=None)
    vin: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    plate_number: str = Field(index=True)
    organization_id: int = Field(foreign_key="organization.id", index=True, ondelete="CASCADE")
    warehouse_stops: Optional[List["WarehouseStop"]] = Relationship(back_populates="vehicle")

class WarehouseStop(SQLModel, table=True):
    __tablename__ = "warehouse_stop"

    id: Optional[int] = Field(default=None, primary_key=True)
    stock_id: str = Field(index=True)
    requester_id: int = Field(foreign_key="users.id")
    request_type: RequestType = Field(default=RequestType.stock_out)
    request_status: RequestStatus = Field(default=RequestStatus.pending)
    request_date: Optional[datetime] = Field(default=None)
    warehouse_id: int = Field(foreign_key="warehouse.id")
    approver_id: Optional[int] = Field(foreign_key="users.id", default=None)
    approve_date: Optional[datetime] = Field(default=None)
    confirmed: Optional[bool] = Field(default=False)
    confirm_date: Optional[datetime] = Field(default=None)
    vehicle_id: Optional[int]= Field(foreign_key="vehicle.id")
    product_id: Optional[int]= Field(foreign_key="product.id")
    stock_type: StockType = Field(default=StockType.regular)
    quantity: int = Field(default=1)
    vehicle: Optional["Vehicle"] = Relationship(back_populates="warehouse_stops")
    warehouse: Optional[Warehouse] = Relationship(back_populates="warehouse_stops")
    # requester: Optional["User"] = Relationship(
    #     sa_relationship_kwargs={"foreign_keys": "[WarehouseStop.requester_id]"},
    #     back_populates="requester_warehouse_stops"
    # )

