from typing import Annotated, Any, Dict, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Body, Path, status
from sqlmodel import Session, select
import traceback
from db import SECRET_KEY, get_session
from models.Warehouse import RequestStatus, RequestType, LogType, StockLog, StockType, Warehouse, WarehouseGroup, WarehouseGroupLink, WarehouseStop, WarehouseStoreAdminLink, Stock, Vehicle
from models.Account import AccessPolicy, Organization
from models.Address import Address, Geolocation
from utils.auth_util import get_current_user, check_permission
from utils.model_converter_util import get_html_types
from utils.util_functions import validate_name, parse_enum, parse_datetime_field, format_date_for_input
from utils.form_db_fetch import fetch_organization_id_and_name, fetch_user_id_and_name, fetch_product_id_and_name,fetch_category_id_and_name, fetch_warehouse_id_and_name, fetch_vehicle_id_and_name, fetch_stocks_id_and_name, fetch_warehouse_group_id_and_name, fetch_admin_warehouse_id_and_name, fetch_address_id_and_name
from utils.warehouse_util import check_warehouse_permission
from utils.get_hierarchy import get_organization_ids_by_scope_group
from models.viewModel.WarehouseView import WarehouseStop as TemplateView

WarehouseItemRequestRouter = wr = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "warehouse-item-request"
db_model = WarehouseStop

endpoint = {
    "get": f"/get-{endpoint_name}s",
    "get_by_status": f"/get-status-{endpoint_name}",
    "get_my_request": f"/get-my-{endpoint_name}",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",
    "update": f"/update-{endpoint_name}",
    "approve_request": f"/approve-{endpoint_name}",
    "reject_request": f"/reject-{endpoint_name}",
    "confirm_request": f"/confirm-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}

role_modules = {   
    "get": ["Inventory Management", "Warehouse-stop"],
    "get_form": ["Inventory Management","Warehouse-stop"],
    "create": ["Inventory Management","Warehouse-stop"],
    "update": ["Inventory Management","Warehouse-stop"],
    "update_status": ["Inventory Management"],
    "confirm": ["Inventory Management","Warehouse-stop"],
    "delete": ["Inventory Management","Warehouse-stop"],
}

request_to_log_type_map = {
    RequestType.stock_out: LogType.stock_out,
    RequestType.transfer: LogType.transfer,
    RequestType.return_defect: LogType.return_defect,
    RequestType.return_normal: LogType.return_normal,
}

@wr.get(endpoint['get_form'])
async def form_warehouse_stop(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        if not check_permission(
            session, "Update", role_modules['get_form'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        data = {
            "id": "",
            "warehouse": fetch_warehouse_id_and_name(session, current_user),
            "product": fetch_product_id_and_name(session, current_user),
            "quantity": "",
            "request_type": {i.value: i.value for i in RequestType},
            "vehicle": fetch_vehicle_id_and_name(session, current_user),
            "stock_type": {i.value: i.value for i in StockType}
            
        }
            
        return {"data": data, "html_types": get_html_types("warehouse_stop")}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.post(endpoint['create'] + "/{stock_id}")
async def create_warehouse_stop(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    valid: TemplateView,
    stock_id: str
):

    try:
        if not check_permission(
            session, "Create",role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
      
       
    
        warehouse_stop = WarehouseStop(
            id = None,
            requester_id = current_user.id,
            request_type = parse_enum(RequestType,valid.request_type, "Request Type"),
            request_date= datetime.now(),
            request_status=parse_enum(RequestStatus, "Pending", "Request Status"),
            vehicle_id = valid.vehicle,
            product_id = valid.product,
            warehouse_id = valid.warehouse,
            quantity = valid.quantity,
            stock_type=parse_enum(StockType, valid.stock_type,"Stock Type"),
            stock_id = stock_id            
        )
        
        
        session.add(warehouse_stop)
        session.commit()
        session.refresh(warehouse_stop)
        
        return {"message": "Warehouse stop created successfully"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.get(endpoint['get']+ "/{id}")
async def get_warehouse_stops(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int

):
  
    try:
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        if not check_warehouse_permission(
            session, "Read", id,current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
      

        warehouse_stops = session.exec(select(WarehouseStop).where((WarehouseStop.warehouse_id==id))).all()
        warehouse_stop_list = []
        for stop in warehouse_stops:

            warehouse_stop_list.append({
                "id": stop.id,
                "warehouse_name": stop.warehouse.warehouse_name,
                "stock": stop.product_id,
                "stock_type": stop.stock_type,
                "quantity": stop.quantity,
                "vehicle": stop.vehicle.name if stop.vehicle else "",
                "requester": stop.requester_id,
                "request_status": stop.request_status,
                "request_type": stop.request_type,
                "request_date": format_date_for_input(stop.request_date),
                "approver": stop.approver_id,
                "approved_date": format_date_for_input(stop.approve_date),
                "confirmed_date": stop.confirm_date,
                "confirmed": stop.confirmed,
                "isRequest": False,
            })
    
        return warehouse_stop_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 
    
@wr.get(endpoint['get_by_id'] + "/{id}")
async def get_warehouse_stop(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int

):
  
    try:
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
     
        warehouse_stop = session.exec(select(WarehouseStop).where(WarehouseStop.id == id)).first()

        if not warehouse_stop:
            raise HTTPException(status_code=404, detail="Warehouse stop not found")
        if not check_warehouse_permission(
            session, "Read", warehouse_stop.warehouse_id,current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )


        return {
                "id": warehouse_stop.id,
                "warehouse": warehouse_stop.warehouse_id,
                "product": warehouse_stop.product_id,
                "quantity": warehouse_stop.quantity,
                "request_type": warehouse_stop.request_type,
                "vehicle": warehouse_stop.vehicle_id,
                "stock_type": warehouse_stop.stock_type,
               
            }  

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 
    

@wr.get(endpoint['get_by_status'] + "/{id}/{status}")
async def get_warehouse_stops_by_status(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,
    status: str

):

    try:
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        if not check_warehouse_permission(
            session, "Read", id,current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
     
        warehouse_stops = session.exec(select(WarehouseStop).where((WarehouseStop.warehouse_id == id)&(WarehouseStop.request_status == parse_enum(RequestStatus,status, "Request Status")))).all()

        warehouse_stop_list = []

        for stop in warehouse_stops:
            warehouse_stop_list.append({
                "id": stop.id,
                "warehouse_name": stop.warehouse.warehouse_name,
                "stock": stop.product_id,
                "stock_type": stop.stock_type,
                "quantity": stop.quantity,
                "vehicle": stop.vehicle.name if stop.vehicle else "",
                "requester": stop.requester_id,
                "request_status": stop.request_status,
                "request_type": stop.request_type,
                "request_date": format_date_for_input(stop.request_date),
                "approver": stop.approver_id,
                "approved_date": format_date_for_input(stop.approve_date),
                "confirmed_date": stop.confirm_date,
                "confirmed": stop.confirmed,
                "isRequest": False,
            })
        

        return warehouse_stop_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 
    
@wr.get(endpoint['get_my_request'])
async def get_my_warehouse_stop_requests(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

):
  
    try:
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        warehouse_stops = session.exec(select(WarehouseStop).where(WarehouseStop.requester_id == current_user.id)).all()

        warehouse_stop_list = []

        for stop in warehouse_stops:
            warehouse_stop_list.append({
                "id": stop.id,
                "warehouse_name": stop.warehouse.warehouse_name,
                "stock": stop.product_id,
                "stock_type": stop.stock_type,
                "quantity": stop.quantity,
                "vehicle": stop.vehicle.name if stop.vehicle else "",
                "requester": stop.requester_id,
                "request_status": stop.request_status,
                "request_type": stop.request_type,
                "request_date": format_date_for_input(stop.request_date),
                "approver": stop.approver_id,
                "approved_date": format_date_for_input(stop.approve_date),
                "confirmed_date": stop.confirm_date,
                "confirmed": stop.confirmed,
                "isRequest": True,
            })
        

        return warehouse_stop_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 
    

@wr.put(endpoint['approve_request'] + "/{id}")
async def approve_warehouse_stops(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int

):
  
    try:
        if not check_permission(
            session, "Read", role_modules['update_status'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        
     
        warehouse_stop = session.exec(select(WarehouseStop).where(WarehouseStop.id == id)).first()

        if not warehouse_stop:
            raise HTTPException(status_code=404, detail="Warehouse stop not found")
        
        if not check_warehouse_permission(
            session, "Update", warehouse_stop.warehouse_id,current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        warehouse_stop.request_status = parse_enum(RequestStatus, "Approved", "Request Status")
        warehouse_stop.approver_id = current_user.id
        warehouse_stop.approve_date = datetime.now()

        session.add(warehouse_stop)
        session.commit()
        session.refresh(warehouse_stop)


        return "Warehouse stop approved successfully"
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 
    
@wr.put(endpoint['reject_request'] + "/{id}")
async def approve_warehouse_stops(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int

):
  
    try:
        if not check_permission(
            session, "Read", role_modules['update_status'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
     
        warehouse_stop = session.exec(select(WarehouseStop).where(WarehouseStop.id == id)).first()

        if not warehouse_stop:
            raise HTTPException(status_code=404, detail="Warehouse stop not found")
        
        if not check_warehouse_permission(
            session, "Update", warehouse_stop.warehouse_id,current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        warehouse_stop.request_status = parse_enum(RequestStatus, "Rejected", "Request Status")
       

        session.add(warehouse_stop)
        session.commit()
        session.refresh(warehouse_stop)


        return "Warehouse stop approved successfully"
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 
    
@wr.put(endpoint['confirm_request'] + "/{id}")
async def confirm_warehouse_stops(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,


):
  
    try:
        if not check_permission(
            session, "Read", role_modules['confirm'], current_user
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

        stock = session.exec(select(Stock).where(Stock.product_id == warehouse_stop.product_id)).first()
        if warehouse_stop.request_type == parse_enum(RequestType, "Transfer", "Request Type") or warehouse_stop.request_type == parse_enum(RequestType, "Stock Out", "Request Type"):

            stock.quantity = stock.quantity - warehouse_stop.quantity
        else:
            stock.quantity = stock.quantity + warehouse_stop.quantity

        session.add(stock)
        session.commit()
        session.refresh(stock)

        stock_log = StockLog(
            stock_id = warehouse_stop.stock_id,
            stock_out_date = datetime.now(),
            warehouse_id = warehouse_stop.warehouse_id,
            product_id = warehouse_stop.product_id,
            quantity = warehouse_stop.quantity,
            stock_type = warehouse_stop.stock_type,
            request_type = warehouse_stop.request_type,
            log_type = request_to_log_type_map.get(warehouse_stop.request_type, LogType.stock_in)  # Default to stock_in
        )

        session.add(stock_log)
        session.commit()
        session.refresh(stock_log)


        return "Warehouse stop confirmed successfully"
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 
    
@wr.put(endpoint['update'])
async def update_warehouse_stop(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    valid: TemplateView
):

    try:
        if not check_permission(
            session, "Create", role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        warehouse_stop = session.exec(select(WarehouseStop).where(WarehouseStop.id == valid.id)).first()

        if not warehouse_stop:
            raise HTTPException(status_code=404, detail="Warehouse stop not found")
        
        
    
        warehouse_stop.request_type = parse_enum(RequestType,valid.request_type, "Request Type")
        warehouse_stop.vehicle_id = valid.vehicle
        warehouse_stop.product_id = valid.product
        warehouse_stop.quantity = valid.quantity
        warehouse_stop.warehouse_id = valid.warehouse
        warehouse_stop.stock_type=parse_enum(StockType, valid.stock_type,"Stock Type")             
      
        session.add(warehouse_stop)
        session.commit()
        session.refresh(warehouse_stop)
        
        return {"message": "Warehouse stop updated successfully"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.delete(endpoint['delete'] + "/{id}")
async def delete_warehouse_stop(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,    
):
  
    try:
        if not check_permission(
            session, "Delete",role_modules['delete'], current_user
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
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 
