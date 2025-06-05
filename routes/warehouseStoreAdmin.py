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
from models.viewModel.WarehouseView import WarehouseStoreAdmin as TemplateView

WarehouseStoreAdminRouter = wr = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "warehouse-storeadmin"
db_model = WarehouseStoreAdminLink

endpoint = {
    "get": f"/get-{endpoint_name}s",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
    "get_update_form": f"/{endpoint_name}-update-form/",
    "create": f"/create-{endpoint_name}",
    "update": f"/update-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}

role_modules = {   
    "get": ["Administrative"],
    "get_form": ["Administrative"],
    "create": ["Administrative"],
    "update": ["Administrative"],
    "delete": ["Administrative"],
}

@wr.get(endpoint['get_form'])
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
        
        store_admin_data = {
                "id": "",
                "warehouse_group": fetch_warehouse_group_id_and_name(session, current_user),
                "store_admins": fetch_user_id_and_name(session, current_user),
            }
            
        return {"data": store_admin_data, "html_types": get_html_types("warehouse-storeadmin-add")}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.post(endpoint['create'])
async def create_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    valid: TemplateView
  
):
    try:
        if not check_permission(
            session, "Create", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        existing_warehouse_storeadmin = session.exec(select(db_model).where(db_model.warehouse_group_id == valid.warehouse_group)).first()

        if existing_warehouse_storeadmin is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse Group Store admin link already exists",
        )
        
       

        for store_admin in valid.store_admins:
            link = WarehouseStoreAdminLink(
                id=None,
                user_id = store_admin,
                warehouse_group_id = valid.warehouse_group,
            )
            session.add(link)
            session.commit()
            session.refresh(link)
        return {"message": "Store admin added successfully."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.get(endpoint['get'])
async def get_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

):
  
    try:
        if not check_permission(
            session, "Read",  role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        warehouse_groups = session.exec(
            select(WarehouseGroup).where(
                WarehouseGroup.id.in_(
                    select(WarehouseStoreAdminLink.warehouse_group_id)
                )
            )
        ).all()

        store_admin_list = []

        for warehouse_group in warehouse_groups:
            store_admin_list.append({
                "id": warehouse_group.id,
                "warehouse_group": warehouse_group.name,
                "store_admins": [store_admin.full_name for store_admin in warehouse_group.store_admins],
            })
        

        return store_admin_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))   
    
@wr.get(endpoint['get_by_id'] + "/{id}")
async def get_template(
    session: SessionDep,
    id: int,
    current_user: UserDep,
    tenant: str,
):
    try:
        if not check_permission(
            session, "Read",  role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        warehouse_group = session.exec(select(WarehouseGroup).where(WarehouseGroup.id == id)).first()
        if not warehouse_group:
            raise HTTPException(status_code=404, detail="Warehouse Group not found")
        
  
        return {
            "warehouse_group": warehouse_group.id,
            "store_admins": [store_admin.id for store_admin in warehouse_group.store_admins],
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@wr.get(endpoint['get_update_form'])
async def form_update_store_admin(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        if not check_permission(
            session, "Update",  role_modules['get_form'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        store_admin_data = {
                "warehouse_group": "",
                "store_admins": fetch_user_id_and_name(session, current_user),
            }
            
        return {"data": store_admin_data, "html_types": get_html_types("warehouse-storeadmin-update")}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))   

@wr.put(endpoint['update'])
async def update_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    valid: TemplateView
  
):

    try:
        if not check_permission(
            session, "Update",  role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
 
        existing_warehouse_group = session.exec(select(WarehouseGroup).where(WarehouseGroup.id == valid.warehouse_group)).first()

        if not existing_warehouse_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse Group does not exsit",
        )
       
         # Step 1: Get existing store admins for the warehouse groups
        existing_store_admins = session.exec(
            select(WarehouseStoreAdminLink.user_id).where(WarehouseStoreAdminLink.warehouse_group_id == valid.warehouse_group)
        ).all()
        print("step 1")
    

        existing_storeadmin_ids = set(existing_store_admins)
        new_storeadmin_ids = set(valid.store_admins)

        # Step 2: Find which ones to add
        to_add = new_storeadmin_ids - existing_storeadmin_ids
        new_links = [
            WarehouseStoreAdminLink(
                user_id=user_id,
                warehouse_group_id = valid.warehouse_group
            )
            for user_id in to_add
        ]
        print("stpe2")

        session.add_all(new_links)
        print(new_links)
        session.commit()

        # Step 3: Optionally, find which ones to remove
        to_remove = existing_storeadmin_ids - new_storeadmin_ids
        if to_remove:
         
            links = session.exec(
            select(WarehouseStoreAdminLink)
            .where(WarehouseStoreAdminLink.warehouse_group_id == valid.warehouse_group)
            .where(WarehouseStoreAdminLink.user_id.in_(to_remove))
            ).all()

            # Delete them
            for link in links:
                session.delete(link)
                session.commit()
        
        return {"message": "Store admin updated successfully"}
    except Exception as e:
        
        raise HTTPException(status_code=400, detail=str(e)) 

@wr.delete(endpoint['delete']+ "/{id}")
async def delete_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,    
):
  
    try:
        if not check_permission(
            session, "Delete",  role_modules['delete'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
    
        store_admin_links = session.exec(
            select(WarehouseStoreAdminLink).where(WarehouseStoreAdminLink.warehouse_group_id == id)
        ).all()

        if not store_admin_links:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store admins with the given Warehouse Group not found",
            )
        
        for link in store_admin_links:
            session.delete(link)
            session.commit()


        return {"message": "Store admins deleted successfully"}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 