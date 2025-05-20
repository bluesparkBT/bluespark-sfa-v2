from typing import Annotated, Any, Dict, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Body, Path, status
from models import Location
from sqlmodel import Session, select


from db import SECRET_KEY, get_session
from models.Warehouse import RequestStatus, RequestType, LogType, StockLog, StockType, Warehouse, WarehouseStop, WarehouseStoreAdminLink, Stock, Vehicle
from models.Account import User
from utils.auth_util import get_current_user, check_permission
from utils.model_converter_util import get_html_types
from utils.util_functions import validate_name, parse_enum, parse_datetime_field, format_date_for_input
from utils.form_db_fetch import fetch_organization_id_and_name, fetch_user_id_and_name, fetch_product_id_and_name,fetch_category_id_and_name, fetch_warehouse_id_and_name, fetch_vehicle_id_and_name, fetch_stocks_id_and_name


WarehouseRouter = wr = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]
request_to_log_type_map = {
    RequestType.stock_out: LogType.stock_out,
    RequestType.transfer: LogType.transfer,
    RequestType.return_defect: LogType.return_defect,
    RequestType.return_normal: LogType.return_normal,
}


@wr.get("/warehouse-form")
async def form_warehouse(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        if not check_permission(
            session, "Create", "Warehouse", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        
        warehouse_data = {
                "id": "",
                "warehouse_name": "",
                "organization": fetch_organization_id_and_name(session, current_user),
                "location": ""
            }
            

        return {"data": warehouse_data, "html_types": get_html_types("warehouse")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.post("/create-warehouse/")
async def create_warehouse(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    warehouse_name: str = Body(...),
    organization: int = Body(...),
    location: str = Body(...),
  
):

    try:
        if not check_permission(
            session, "Create", "Warehouse", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        existing_warehouse = session.exec(select(Warehouse).where(Warehouse.warehouse_name == warehouse_name)).first()

        if existing_warehouse is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse already registered",
        )
        #Check Validity
        
        if validate_name(warehouse_name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse name is not valid",
        )

        cleaned = location.strip("()")
        lat_str, lon_str = cleaned.split(",")

        location_db = Location(
            id = None,
            latitude = float(lat_str),
            longitude= float(lon_str)
        )

        session.add(location_db)
        session.commit()
        session.refresh(location_db)
        
        
        warehouse = Warehouse(
            id = None,
            warehouse_name = warehouse_name,
            organization_id = organization,
            location_id = location_db.id,
        )
        
        
        session.add(warehouse)
        session.commit()
        session.refresh(warehouse)
        
        return warehouse.id
    except Exception as e:
        
        raise HTTPException(status_code=400, detail=str(e))   
    
@wr.get("/warehouse-storeadmin-form/")
async def form_warehouse_storeadmin(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        if not check_permission(
            session, "Create", "Warehouse", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        data = {"warehouse_id":"",
                "store_admin": fetch_user_id_and_name(session, current_user)
                }
     
        return {"data": data, "html_types": get_html_types("warehouse_storeadmin")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.post("/assign-storeadmin")
async def assign_store_admin(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    warehouse_id: int = Body(...),
    store_admin: List[int] = Body(...)
):
    try:
        if not check_permission(
            session, "Update", "Warehouse", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        warehouse = session.exec(select(Warehouse).where(Warehouse.id == warehouse_id)).first()

        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Warehouse not found",
            )
        print("step 0")
        # Step 1: Get existing store admins for the warehouse
        existing_store_admins = session.exec(
            select(WarehouseStoreAdminLink.user_id).where(WarehouseStoreAdminLink.warehouse_id == warehouse_id)
        ).all()
        print("step 1")

        existing_store_admin_ids = set(existing_store_admins)
        new_store_admin_ids = set(store_admin)

        # Step 2: Find which ones to add
        to_add = new_store_admin_ids - existing_store_admin_ids
        new_links = [
            WarehouseStoreAdminLink(
                warehouse_id=warehouse_id,
                user_id=user_id
            )
            for user_id in to_add
        ]
        print("stpe2")

        session.add_all(new_links)

        # Step 3: Optionally, find which ones to remove
        to_remove = existing_store_admin_ids - new_store_admin_ids
        if to_remove:
            session.exec(
                select(WarehouseStoreAdminLink)
                .where(WarehouseStoreAdminLink.warehouse_id == warehouse_id)
                .where(WarehouseStoreAdminLink.user_id.in_(to_remove))
            ).all()

            for link in session.exec(
                select(WarehouseStoreAdminLink)
                .where(WarehouseStoreAdminLink.warehouse_id == warehouse_id)
                .where(WarehouseStoreAdminLink.user_id.in_(to_remove))
            ):
                session.delete(link)
        print("stpe3")

        session.commit()


        return "Warehouse store admin added successfully"
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@wr.get("/get-warehouses/")
async def get_warehouses(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

):
  
    try:
        if not check_permission(
            session, "Read", "Warehouse", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        statement = (
            select(Warehouse)
            .join(WarehouseStoreAdminLink)
            .where(WarehouseStoreAdminLink.user_id == current_user.id)
        )
        warehouses = session.exec(statement).all()

        warehouse_list = []

        for warehouse in warehouses:
            warehouse_list.append({
                "id": warehouse.id,
                "warehouse_name": warehouse.warehouse_name,
                "organization": warehouse.organization.organization_name,
                "store_admins": [store_admin.fullname for store_admin in warehouse.store_admins],
            })
        

        return warehouse_list

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))   
    
@wr.get("/get-warehouse/{id}")
async def get_warehouse(
    session: SessionDep,
    id: int,
    current_user: UserDep,
    tenant: str,
):
    try:
        if not check_permission(
            session, "Read", "Warehouse", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        warehouse = session.exec(select(Warehouse).where(Warehouse.id == id)).first()
        if not warehouse:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        
        location_db = session.exec(select(Location).where(Location.id == warehouse.location_id)).first()
        location_str = f"({location_db.latitude},{location_db.longitude})"
  
        return {
            "id": warehouse.id,
            "warehouse_name": warehouse.warehouse_name,
            "organization": warehouse.organization_id,
            "store_admins": [store_admin.id for store_admin in warehouse.store_admins],
            "location":location_str
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@wr.put("/update-warehouse/")
async def update_warehouse(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int = Body(...),
    warehouse_name: str = Body(...),
    organization: int = Body(...),
    location: str = Body(...)
  
):

    try:
        if not check_permission(
            session, "Update", "Warehouse", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        existing_warehouse = session.exec(select(Warehouse).where(Warehouse.id == id)).first()

        if not existing_warehouse:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse does not exsit",
        )
        #Check Validity
        
        if validate_name(warehouse_name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse name is not valid",
        )

        cleaned = location.strip("()")
        lat_str, lon_str = cleaned.split(",")

        location_db = Location(
            id = None,
            latitude = float(lat_str),
            longitude= float(lon_str)
        )

        session.add(location_db)
        session.commit()
        session.refresh(location_db)

        existing_warehouse.warehouse_name = warehouse_name
        existing_warehouse.organization_id = organization
        existing_warehouse.location_id = location_db.id

        
        session.add(existing_warehouse)
        session.commit()
        session.refresh(existing_warehouse)
        
        return existing_warehouse.id
    except Exception as e:
        
        raise HTTPException(status_code=400, detail=str(e)) 

@wr.delete("/delete-warehouse/{id}")
async def delete_warehouse(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,    
):
  
    try:
        if not check_permission(
            session, "Delete", "Warehouse", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
    
        warehouse = session.get(Warehouse, id)

        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Warehouse not found",
            )
        
        store_admin_links = session.exec(
            select(WarehouseStoreAdminLink).where(WarehouseStoreAdminLink.warehouse_id == id)
        ).all()

        for link in store_admin_links:
            session.delete(link)
            session.commit()

        stocks = session.exec(
            select(Stock).where(Stock.warehouse_id == id)
        ).all()

        for stock in stocks:
            stops= session.exec(
                    select(WarehouseStop).where(WarehouseStop.stock_id== stock.id)
                        ).all()
            for stop in stops:
                session.delete(stop)
                session.commit()

            stock_log = session.exec(
                    select(StockLog).where(StockLog.stock_id == stock.id)
                ).all()

            for log in stock_log:
                session.delete(log)
                session.commit()

            session.delete(stock)
            session.commit()


       
        session.delete(warehouse)
        session.commit()

        return {"message": "Warehouse deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    
@wr.get("/stock-form")
async def form_stock(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        if not check_permission(
            session, "Create", "Stock", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        
        stock_data = {
                "id": "",
                "warehouse": fetch_warehouse_id_and_name(session, current_user),
                "product": fetch_product_id_and_name(session, current_user),
                "category": fetch_category_id_and_name(session, current_user),
                "sub_category": fetch_category_id_and_name(session, current_user),
                "quantity": "",
                "stock_type": {i.value : i.value for i in StockType}
            }
            

        return {"data": stock_data, "html_types": get_html_types("stock")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@wr.post("/add-stock/")
async def add_stock(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    warehouse: int = Body(...),
    product: int = Body(...),
    category: int = Body(...),
    sub_category: int = Body(...),
    quantity: int = Body(...),
    stock_type: str = Body(...)
  
):

    try:
        if not check_permission(
            session, "Create", "Stock", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        existing_stock = session.exec(select(Stock)
                                      .where((Stock.product_id == product)&
                                             (Stock.warehouse_id==warehouse))).first()

        if existing_stock is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock for the provided product already exists",
        )
        
        
        stock = Stock(
            id=None,
            warehouse_id=warehouse,
            product_id=product,
            category_id=category,
            subcategory_id=sub_category,
            quantity=quantity,
            stock_type= parse_enum(StockType,stock_type, "Stock Type"),
            date_added=datetime.now()

        )

        session.add(stock)
        session.commit()
        session.refresh(stock)

        stock_log = StockLog(
            stock_id = stock.id,
            stock_in_date = datetime.now(),
            log_type = LogType.stock_in,
        )

        session.add(stock_log)
        session.commit()
        session.refresh(stock_log)
      
        
        return {"message": "Stock added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.get("/get-stocks/")
async def get_stocks(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

):
  
    try:
        if not check_permission(
            session, "Read", "Stock", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        statement = (
            select(Stock)
            .join(Warehouse, Stock.warehouse_id == Warehouse.id)
            .join(WarehouseStoreAdminLink, WarehouseStoreAdminLink.warehouse_id == Warehouse.id)
            .where(WarehouseStoreAdminLink.user_id == current_user.id))  
    
        stocks = session.exec(statement).all()

        stock_list = []

        for stock in stocks:
            stock_list.append({
                "id": stock.id,
                "warehouse": stock.warehouse.warehouse_name,
                "product": stock.product.name,
                "category": stock.category.name,
                "sub_category": stock.subcategory.name,
                "quantity": stock.quantity,
                "stock_type": stock.stock_type,
                "date_added": format_date_for_input(stock.date_added)
            })
        return stock_list

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    

@wr.get("/get-stock/{id}")
async def get_stock(
    session: SessionDep,
    id: int,
    current_user: UserDep,
    tenant: str,
):
    try:
        if not check_permission(
            session, "Read", "Stock", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        stock = session.exec(select(Stock).where(Stock.id == id)).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
  
        return {
            "id": stock.id,
            "warehouse": stock.warehouse_id,
            "product": stock.product_id,
            "category": stock.category_id,
            "sub_category": stock.subcategory_id,
            "quantity": stock.quantity,
            "stock_type": stock.stock_type,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.put("/update-stock/")
async def update_stock(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int = Body(...),
    warehouse: int = Body(...),
    product: int = Body(...),
    category: int = Body(...),
    sub_category: int = Body(...),
    quantity: int = Body(...),
    stock_type: str = Body(...)
  
):

    try:
        if not check_permission(
            session, "Update", "Stock", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        existing_stock = session.exec(select(Stock).where((Stock.id == id))).first()

        if not existing_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock does not exist",
        )
        
        
        existing_stock.warehouse_id=warehouse
        existing_stock.product_id=product
        existing_stock.category_id=category
        existing_stock.subcategory_id=sub_category
        existing_stock.quantity=quantity
        existing_stock.stock_type= parse_enum(StockType,stock_type, "Stock Type")
      

        session.add(existing_stock)
        session.commit()
        session.refresh(existing_stock)

        return {"message": "Stock updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@wr.delete("/delete-stock/{id}")
async def delete_stock(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,    
):
  
    try:
        if not check_permission(
            session, "Delete", "Stock", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
    
        stock = session.get(Stock, id)

        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stock not found",
            )
        
        stops = session.exec(
            select(WarehouseStop).where(WarehouseStop.stock_id == id)
        ).all()

        stock_log = session.exec(
            select(StockLog).where(StockLog.stock_id == id)
        ).all()

        for stop in stops:
            session.delete(stop)
            session.commit()


        for log in stock_log:
            session.delete(log)
            session.commit()
 
        session.delete(stock)
        session.commit()

        return {"message": "Stock deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    
@wr.get("/get-stock-logs/{id}")
async def get_stock_logs(
    session: SessionDep,
    id: int,
    current_user: UserDep,
    tenant: str,
):
    try:
        if not check_permission(
            session, "Read", "Stock", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        stock = session.exec(select(Stock).where(Stock.id == id)).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        stock_log_list=[]

        for log in stock.stock_logs:
            stock_log_list.append({
                "id":log.id,
                "product":stock.product.name,
                "stock_in_date": format_date_for_input(log.stock_in_date),
                "stock_out_date": format_date_for_input(log.stock_out_date),
                "log_type": log.log_type,
                "request_type": log.request_type



            })
        return stock_log_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.get("/warehouse-stop-form")
async def form_warehouse_stop(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        if not check_permission(
            session, "Create", "Warehouse-stop", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        data = {
            "id": "",
            "stock": fetch_stocks_id_and_name(session, current_user),
            "quantity": "",
            "request_type": {i.value: i.value for i in RequestType},
            "vehicle": fetch_vehicle_id_and_name(session, current_user),
            "stock_type": {i.value: i.value for i in StockType}
            
        }
            
        return {"data": data, "html_types": get_html_types("warehouse_stop")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.post("/create-warehouse-stop/")
async def create_warehouse_stop(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    request_type: str = Body(...),
    vehicle: int = Body(...),
    stock: int = Body(...),
    quantity: int = Body(...),
    stock_type: str = Body(...)
):

    try:
        if not check_permission(
            session, "Create", "Warehouse-stop", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        stock_data = session.exec(select(Stock).where(Stock.id == stock)).first()

        if quantity > stock_data.quantity:
            raise HTTPException(
                status_code=400, detail="Not enough stock amount"
            )
    
        warehouse_stop = WarehouseStop(
            id = None,
            requester_id = current_user.id,
            request_type = parse_enum(RequestType,request_type, "Request Type"),
            request_date= datetime.now(),
            request_status=parse_enum(RequestStatus, "Pending", "Request Status"),
            vehicle_id = vehicle,
            stock_id=stock,
            quantity = quantity,
            stock_type=parse_enum(StockType, stock_type,"Stock Type")             
        )
        
        
        session.add(warehouse_stop)
        session.commit()
        session.refresh(warehouse_stop)
        
        return {"message": "Warehouse stop created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.get("/get-warehouse-stops/")
async def get_warehouse_stops(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

):
  
    try:
        if not check_permission(
            session, "Read", "Warehouse-stop", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        statement = (
            select(WarehouseStop)
            .join(Stock, WarehouseStop.stock_id == Stock.id)
            .join(Warehouse, Stock.warehouse_id == Warehouse.id)
            .join(WarehouseStoreAdminLink, WarehouseStoreAdminLink.warehouse_id == Warehouse.id)
            .where(WarehouseStoreAdminLink.user_id == current_user.id)) 
        
        warehouse_stops = session.exec(statement).all()

        warehouse_stop_list = []

        for stop in warehouse_stops:
            warehouse_stop_list.append({
                "id": stop.id,
                "warehouse_name": stop.stock.warehouse.warehouse_name,
                "stock": stop.stock.product.name,
                "stock_type": stop.stock_type,
                "quantity": stop.quantity,
                "vehicle": stop.vehicle.name,
                "requester": stop.requester.fullname,
                "request_status": stop.request_status,
                "request_type": stop.request_type,
                "request_date": format_date_for_input(stop.request_date),
                "approver": stop.approver.fullname if stop.approver_id is not None else "",
                "approved_date": format_date_for_input(stop.approve_date),
                "confirmed_date": stop.confirm_date,
                "confirmed": stop.confirmed
            })
        

        return warehouse_stop_list

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    
@wr.get("/get-warehouse-stop/{id}")
async def get_warehouse_stop(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int

):
  
    try:
        if not check_permission(
            session, "Read", "Warehouse-stop", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
     
        warehouse_stop = session.exec(select(WarehouseStop).where(WarehouseStop.id == id)).first()

        if not warehouse_stop:
            raise HTTPException(status_code=404, detail="Warehouse stop not found")

       

        return {
                "id": warehouse_stop.id,
                "request_type": warehouse_stop.request_type,
                "stock": warehouse_stop.stock_id,
                "vehicle": warehouse_stop.vehicle_id,
                "stock_type": warehouse_stop.stock_type,
                "quantity": warehouse_stop.quantity,
            }  

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    

@wr.get("/get-warehouse-stops/{status}")
async def get_warehouse_stops_by_status(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    status: str

):
  
    try:
        if not check_permission(
            session, "Read", "Warehouse-stop", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        statement = (
            select(WarehouseStop)
            .join(Stock, WarehouseStop.stock_id == Stock.id)
            .join(Warehouse, Stock.warehouse_id == Warehouse.id)
            .join(WarehouseStoreAdminLink, WarehouseStoreAdminLink.warehouse_id == Warehouse.id)
            .where(WarehouseStoreAdminLink.user_id == current_user.id)
            .where(WarehouseStop.request_status == parse_enum(RequestStatus,status, "Request Status"))) 
        
        warehouse_stops = session.exec(statement).all()

        warehouse_stop_list = []

        for stop in warehouse_stops:
            warehouse_stop_list.append({
                "id": stop.id,
                "warehouse_name": stop.stock.warehouse.warehouse_name,
                "stock": stop.stock.product.name,
                "stock_type": stop.stock_type,
                "quantity": stop.quantity,
                "vehicle": stop.vehicle.name,
                "requester": stop.requester.fullname,
                "request_status": stop.request_status,
                "request_type": stop.request_type,
                "request_date": format_date_for_input(stop.request_date),
                "approver": stop.approver.fullname if stop.approver_id is not None else "",
                "approved_date": format_date_for_input(stop.approve_date),
                "confirmed_date": stop.confirm_date,
                "confirmed": stop.confirmed
            })
        

        return warehouse_stop_list

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    
@wr.get("/get-warehouse-stops/request/")
async def get_my_warehouse_stop_requests(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

):
  
    try:
        if not check_permission(
            session, "Read", "Warehouse-stop", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        warehouse_stops = session.exec(select(WarehouseStop).where(WarehouseStop.requester_id == current_user.id)).all()

        warehouse_stop_list = []

        for stop in warehouse_stops:
            warehouse_stop_list.append({
                "id": stop.id,
                "warehouse_name": stop.stock.warehouse.warehouse_name,
                "stock": stop.stock.product.name,
                "stock_type": stop.stock_type,
                "quantity": stop.quantity,
                "vehicle": stop.vehicle.name,
                "requester": stop.requester.fullname,
                "request_status": stop.request_status,
                "request_type": stop.request_type,
                "request_date": format_date_for_input(stop.request_date),
                "approver": stop.approver.fullname if stop.approver_id is not None else "",
                "approved_date": format_date_for_input(stop.approve_date),
                "confirmed_date": format_date_for_input(stop.confirm_date),
                "confirmed": stop.confirmed
            })
        

        return warehouse_stop_list

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    

@wr.put("/warehouse-stops/approve/{id}")
async def approve_warehouse_stops(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int

):
  
    try:
        if not check_permission(
            session, "Read", "Warehouse-stop", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
     
        warehouse_stop = session.exec(select(WarehouseStop).where(WarehouseStop.id == id)).first()

        if not warehouse_stop:
            raise HTTPException(status_code=404, detail="Warehouse stop not found")
        
        warehouse_stop.request_status = parse_enum(RequestStatus, "Approved", "Request Status")
        warehouse_stop.approver_id = current_user.id
        warehouse_stop.approve_date = datetime.now()

        session.add(warehouse_stop)
        session.commit()
        session.refresh(warehouse_stop)


        return "Warehouse stop approved successfully"
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    
@wr.put("/warehouse-stops/reject/{id}")
async def approve_warehouse_stops(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int

):
  
    try:
        if not check_permission(
            session, "Read", "Warehouse-stop", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
     
        warehouse_stop = session.exec(select(WarehouseStop).where(WarehouseStop.id == id)).first()

        if not warehouse_stop:
            raise HTTPException(status_code=404, detail="Warehouse stop not found")
        
        warehouse_stop.request_status = parse_enum(RequestStatus, "Rejected", "Request Status")
       

        session.add(warehouse_stop)
        session.commit()
        session.refresh(warehouse_stop)


        return "Warehouse stop approved successfully"
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    
@wr.put("/warehouse-stops/confirm/{id}")
async def confirm_warehouse_stops(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int

):
  
    try:
        if not check_permission(
            session, "Read", "Warehouse-stop", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        warehouse_stop = session.exec(
            select(WarehouseStop).where(
                (WarehouseStop.id == id) & 
                (WarehouseStop.request_status == parse_enum(RequestStatus, "Approved", "Request Status"))
            )
        ).first()


        if not warehouse_stop:
            raise HTTPException(status_code=404, detail="Warehouse stop not found or not approved")
        
        warehouse_stop.confirmed = True
        warehouse_stop.confirm_date = datetime.now()

        session.add(warehouse_stop)
        session.commit()
        session.refresh(warehouse_stop)

        stock = session.exec(select(Stock).where(Stock.id == warehouse_stop.stock_id)).first()
        stock.quantity = stock.quantity - warehouse_stop.quantity

        session.add(stock)
        session.commit()
        session.refresh(stock)

        stock_log = StockLog(
            stock_id = stock.id,
            stock_out_date = datetime.now(),
            request_type = warehouse_stop.request_type,
            log_type = request_to_log_type_map.get(warehouse_stop.request_type, LogType.stock_in)  # Default to stock_in
        )

        session.add(stock_log)
        session.commit()
        session.refresh(stock_log)


        return "Warehouse stop confirmed successfully"
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    
@wr.put("/update-warehouse-stop/")
async def update_warehouse_stop(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int = Body(...),
    request_type: str = Body(...),
    vehicle: int = Body(...),
    stock: int = Body(...),
    quantity: int = Body(...),
    stock_type: str = Body(...)
):

    try:
        if not check_permission(
            session, "Create", "Warehouse-stop", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        warehouse_stop = session.exec(select(WarehouseStop).where(WarehouseStop.id == id)).first()

        if not warehouse_stop:
            raise HTTPException(status_code=404, detail="Warehouse stop not found")
        
        stock_data = session.exec(select(Stock).where(Stock.id == stock)).first()

        if quantity > stock_data.quantity:
            raise HTTPException(
                status_code=400, detail="Not enough stock amount"
            )
    
        warehouse_stop.request_type = parse_enum(RequestType,request_type, "Request Type")
        warehouse_stop.vehicle_id = vehicle
        warehouse_stop.stock_id=stock
        warehouse_stop.quantity = quantity
        warehouse_stop.stock_type=parse_enum(StockType, stock_type,"Stock Type")             
      
        session.add(warehouse_stop)
        session.commit()
        session.refresh(warehouse_stop)
        
        return {"message": "Warehouse stop updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.delete("/delete-warehouse_stop/{id}")
async def delete_warehouse_stop(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,    
):
  
    try:
        if not check_permission(
            session, "Delete", "Warehouse-stop", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
    
        warehouse_stop = session.get(WarehouseStop, id)

        if not warehouse_stop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Warehouse stop not found",
            )
 
        session.delete(warehouse_stop)
        session.commit()

        return {"message": "Warehouse stop deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    

    


        


