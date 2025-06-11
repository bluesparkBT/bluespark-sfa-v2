from typing import Annotated, Any, Dict, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Body, Path, status
from sqlmodel import Session, select
import traceback
from collections import defaultdict
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
from models.viewModel.WarehouseView import Stock as TemplateView

StockLogRouter = sr = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "stock-log"
db_model = StockLog

endpoint = {
    "get": f"/get-{endpoint_name}s",
    "get_current": f"/get-current-{endpoint_name}",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",
    "update": f"/update-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}

role_modules = {   
    "get": ["Inventory Management"],
    "get_form": ["Inventory Management"],
    "create": ["Inventory Management"],
    "update": ["Inventory Management"],
    "delete": ["Inventory Management"],
}
    
@sr.post(endpoint['create']+ "/{id}/{stock_id}")
async def create_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,
    stock_id: str,
    valid: TemplateView
):

    try:
        if not check_permission(
            session, "Create", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        if not check_warehouse_permission(
            session, "Create", id,current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
      
        stock_log = StockLog(
            stock_id = stock_id,
            warehouse_id=id,
            product_id = valid.product,
            quantity = valid.quantity,
            stock_in_date = datetime.now(),
            log_type = LogType.stock_in,
            stock_type = valid.stock_type
        )

        session.add(stock_log)
        session.commit()
        session.refresh(stock_log)
      
        
        return {"message": "Stock added successfully"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@sr.get(endpoint['get'] + "/{id}")
async def get_template(
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
    
        stocks = session.exec(select(StockLog).where(StockLog.warehouse_id == id)).all()

        grouped_stocks = defaultdict(list)

        # Group by stock_id
        for stock in stocks:
            grouped_stocks[stock.stock_id].append(stock)

        stock_list = []

        for stock_id, group in grouped_stocks.items():
            # Assume all entries in group share same warehouse and dates
            first = group[0]

            products = []
            quantities = []
            log_types = []
            request_types = []

            for stock in group:
                products.append(str(stock.product.name))
                quantities.append(str(stock.quantity))
                log_types.append(stock.log_type)
                if stock.request_type:
                    request_types.append(stock.request_type)

            stock_list.append({
                "id": stock_id,
                "warehouse": first.warehouse.warehouse_name,
                "product": "<br/><br/>".join(products),
                "quantity": "<br/><br/>".join(quantities),
                "stock_in_date": format_date_for_input(first.stock_in_date),
                "stock_out_date": format_date_for_input(first.stock_out_date),
                "log_type": "<br/><br/>".join(log_types),
                "request_type": "<br/><br/>".join(request_types) if len(request_types) > 0 else ""
            })
        return stock_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 
    
    
@sr.get(endpoint['get_current'] + "/{id}")
async def get_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: str

):
  
    try:
        if not check_permission(
            session, "Read", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
       
    
        stocks = session.exec(select(StockLog).where(StockLog.stock_id == id)).all()

        stock_list = []

        for stock in stocks:
            stock_list.append({
                "id": stock.id,
                "warehouse": stock.warehouse.warehouse_name,
                "product": stock.product_id,
                "quantity": stock.quantity,
                "stock_in_date": format_date_for_input(stock.stock_in_date),
                "stock_out_date": format_date_for_input(stock.stock_out_date),
                "log_type": stock.log_type,
                "request_type": stock.request_type,
            })
        return stock_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 
    
@sr.put(endpoint['update']+"/{stock_id}")
async def update_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    stock_id: str,
    valid: TemplateView
  
):

    try:
        if not check_permission(
            session, "Update", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
       
        existing_stock = session.exec(select(StockLog).where((StockLog.product_id == valid.product)&(StockLog.stock_id == stock_id))).first()
        if not check_warehouse_permission(
            session, "Create", existing_stock.warehouse_id,current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        if not existing_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock log does not exist",
        )

        
        existing_stock.product_id =valid.product
        existing_stock.quantity = valid.quantity
        existing_stock.stock_type = valid.stock_type
       

        session.add(existing_stock)
        session.commit()
        session.refresh(existing_stock)

        return {"message": "Stock updated successfully"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@sr.get(endpoint['get_by_id'] + "/{id}")
async def get_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,
):
    try:
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        stock_log = session.exec(select(StockLog).where(StockLog.id == id)).first()
        # stock = session.exec(select(Stock).where(Stock.product_id == stock_log.product_id)).first()
        if not stock_log:
            raise HTTPException(status_code=404, detail="Stock log not found")
        print("stock log: ", stock_log)
     
  
        return {
            "id": stock_log.id,
            "product": stock_log.product_id,
            "quantity": stock_log.quantity,
            "stock_type": stock_log.stock_type,
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    

# @sr.get(endpoint['get_by_id'] + "/{id}")
# async def get_template(
#     session: SessionDep,
#     id: int,
#     current_user: UserDep,
#     tenant: str,
# ):
#     try:
#         if not check_permission(
#             session, "Read", role_modules['get'], current_user
#             ):
#             raise HTTPException(
#                 status_code=403, detail="You Do not have the required privilege"
#             )
#         stock = session.exec(select(StockLog).where(StockLog.product_id == id)).first()
#         if not stock:
#             raise HTTPException(status_code=404, detail="Stock log not found")
#         if not check_warehouse_permission(
#             session, "Read", stock.warehouse_id,current_user
#         ):
#             raise HTTPException(
#                 status_code=403, detail="You Do not have the required privilege"
#             )
  
#         return {
#             "id": stock.id,
#             "warehouse": stock.warehouse_id,
#             "product": stock.product_id,
#             "quantity": stock.quantity,
#             "stock_type": stock.stock_type,
#         }
#     except Exception as e:
#         traceback.print_exc()
#         raise HTTPException(status_code=400, detail=str(e))
    

    

@sr.delete(endpoint['delete']+ "/{id}")
async def delete_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,    
):
  
    try:
        if not check_permission(
            session, "Delete", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
    
        stock_log = session.get(StockLog, id)
        if not check_warehouse_permission(
            session, "Create", stock_log.warehouse_id,current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        if not stock_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stock not found",
            )
       
        
       

        
        session.delete(stock_log)
        session.commit()

        return {"message": "Stock log deleted successfully"}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 
