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
from models.viewModel.WarehouseView import Stock as TemplateView

StockRouter = sr = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "stock"
db_model = Stock

endpoint = {
    "get": f"/get-{endpoint_name}s",
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

@sr.get(endpoint['get_form'])
async def get_template_form(
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
        
        stock_data = {
                "id": "",
                "product": fetch_product_id_and_name(session, current_user),
                "quantity": "",
                "stock_type": {i.value : i.value for i in StockType}
            }
            

        return {"data": stock_data, "html_types": get_html_types("stock")}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    

@sr.get(endpoint['create']+ "/{id}")
async def create_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: str,
):

    try:
        if not check_permission(
            session, "Create", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

      

        logs = session.exec(select(StockLog).where((StockLog.stock_id == id))).all()

        for log in logs:
            stock = session.exec(select(Stock).where((Stock.product_id == log.product_id))).first()
            if stock:
                stock.quantity = stock.quantity + log.quantity
                stock.stock_type =  log.stock_type
                session.add(stock)
                session.commit()
                session.refresh(stock)
            else:
                stock = Stock(
                    id=None,
                    warehouse_id=log.warehouse_id,
                    product_id=log.product_id,
                    quantity=log.quantity,
                    stock_type= parse_enum(StockType,log.stock_type, "Stock Type"),
                    date_added=datetime.now()
                )
                session.add(stock)
                session.commit()
                session.refresh(stock)
      
        
        return {"message": "Stock added successfully"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

#checked    
@sr.get(endpoint['get']+ "/{id}")
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
        if not check_warehouse_permission(
            session, "Read", id,current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
      

        stocks = session.exec(select(Stock).where((Stock.warehouse_id==id))).all()
    

        stock_list = []
        if stocks:

            for stock in stocks:
                stock_list.append({
                    "id": stock.id,
                    "warehouse": stock.warehouse.warehouse_name,
                    "product": stock.product.name,
                    "quantity": stock.quantity,
                    "stock_type": stock.stock_type,
                    "date_added": format_date_for_input(stock.date_added)
                })
        return stock_list

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
        
        stock = session.exec(select(Stock).where(Stock.id == id)).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        if not check_warehouse_permission(
            session, "Read", stock.warehouse_id,current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
  
        return {
            "id": stock.id,
            "product": stock.product_id,
            "quantity": stock.quantity,
            "stock_type": stock.stock_type,
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@sr.put(endpoint['update']+ "/{id}")
async def update_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,
    valid: TemplateView
  
):

    try:
        if not check_permission(
            session, "Update", role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        existing_stock = session.exec(select(Stock).where((Stock.id == valid.id))).first()

        if not existing_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock does not exist",
        )
        if not check_warehouse_permission(
            session, "Update", id,current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        existing_stock.product_id=valid.product
        existing_stock.quantity=valid.quantity
        existing_stock.stock_type= parse_enum(StockType,valid.stock_type, "Stock Type")
      

        session.add(existing_stock)
        session.commit()
        session.refresh(existing_stock)

        return {"message": "Stock updated successfully"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    

@sr.delete(endpoint['delete']+ "/{id}")
async def delete_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,    
):
  
    try:
        if not check_permission(
            session, "Delete", role_modules['delete'], current_user
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
        if not check_warehouse_permission(
            session, "Delete", stock.warehouse_id,current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        # stops = session.exec(
        #     select(WarehouseStop).where(WarehouseStop.stock_id == id)
        # ).all()

        # stock_log = session.exec(
        #     select(StockLog).where(StockLog.stock_id == id)
        # ).all()

        # for stop in stops:
        #     session.delete(stop)
        #     session.commit()


        # for log in stock_log:
        #     session.delete(log)
        #     session.commit()
 
        session.delete(stock)
        session.commit()

        return {"message": "Stock deleted successfully"}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 
    
# @sr.get("/get-stock-logs/{id}")
# async def get_stock_logs(
#     session: SessionDep,
#     id: int,
#     current_user: UserDep,
#     tenant: str,
# ):
#     try:
#         if not check_permission(
#             session, "Read", "Inventory Management", current_user
#             ):
#             raise HTTPException(
#                 status_code=403, detail="You Do not have the required privilege"
#             )
#         stock = session.exec(select(Stock).where(Stock.id == id)).first()
#         if not stock:
#             raise HTTPException(status_code=404, detail="Stock not found")
#         if not check_warehouse_permission(
#             session, "Read", stock.warehouse_id,current_user
#         ):
#             raise HTTPException(
#                 status_code=403, detail="You Do not have the required privilege"
#             )
        
#         stock_log_list=[]

#         for log in stock.stock_logs:
#             stock_log_list.append({
#                 "id":log.id,
#                 "product":stock.product.name,
#                 "stock_in_date": format_date_for_input(log.stock_in_date),
#                 "stock_out_date": format_date_for_input(log.stock_out_date),
#                 "log_type": log.log_type,
#                 "request_type": log.request_type



#             })
#         return stock_log_list
#     except Exception as e:
#         traceback.print_exc()
#         raise HTTPException(status_code=400, detail=str(e))