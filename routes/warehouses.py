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
from models.viewModel.WarehouseView import Warehouse as TemplateView

WarehouseRouter = wr = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "warehouse"
db_model = Warehouse

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
    "get_form": ["Administrative"],
    "create": ["Administrative"],
    "update": ["Administrative"],
    "delete": ["Administrative"],
}

@wr.get(endpoint['get_form'])
async def form_warehouse(
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
        
        
        warehouse_data = {
                "id": "",
                "warehouse_name": "",
                "organization": fetch_organization_id_and_name(session, current_user),
                "address": fetch_address_id_and_name(session,current_user),
                "landmark":"",
                "latitude": "",
                "longitude": ""
            }
            
        return {"data": warehouse_data, "html_types": get_html_types("warehouse")}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.post(endpoint['create'])
async def create_warehouse(
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
        existing_warehouse = session.exec(select(db_model).where(db_model.warehouse_name == valid.warehouse_name)).first()

        if existing_warehouse is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse already registered",
        )
      
        location_db = Geolocation(
            id = None,
            latitude = valid.latitude,
            longitude= valid.longitude,
        )
        session.add(location_db)
        session.commit()
        session.refresh(location_db)


        
        warehouse = Warehouse(
            id = None,
            warehouse_name = valid.warehouse_name,
            organization_id = valid.organization,
            address_id = valid.address,
            landmark = valid.landmark,
            location_id = location_db.id
        )
        
        session.add(warehouse)
        session.commit()
        session.refresh(warehouse)

        # add the created warehouse to the warehouse group assigned to the system admin
        organization = session.exec(select(Organization).where(Organization.tenant_hashed == tenant)).first()
        print("organization", organization)
        warehouse_group = session.exec(
            select(WarehouseGroup).where(
                (WarehouseGroup.organization_id == organization.id) &
                (WarehouseGroup.name == f"{organization.name} Admin Warehouse Group")
            )
        ).first()
        if warehouse_group is not None:
            link = WarehouseGroupLink(
                id=None,
                warehouse_id=warehouse.id,
                warehouse_group_id=warehouse_group.id
            )

            session.add(link)
            session.commit()
            session.refresh(link)

        
        return warehouse.id
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))   

    

@wr.get(endpoint['get'])
async def get_warehouses(
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


        # Step 1: find warehouse IDs the current user is linked to via a deny access policyAdd commentMore actions
        deny_warehouses_subquery = (
            select(WarehouseGroupLink.warehouse_id)
            .join(WarehouseStoreAdminLink, WarehouseStoreAdminLink.warehouse_group_id == WarehouseGroupLink.warehouse_group_id)
            .join(WarehouseGroup, WarehouseGroup.id == WarehouseGroupLink.warehouse_group_id)
            .where(
                WarehouseStoreAdminLink.user_id == current_user.id,
                WarehouseGroup.access_policy == "deny"  # or AccessPolicy.deny if enum
            )
        )

        # Step 2: return warehouses linked to the user, excluding the above
        statement = (
            select(Warehouse)
            .join(WarehouseGroupLink, WarehouseGroupLink.warehouse_id == Warehouse.id)
            .join(WarehouseStoreAdminLink, WarehouseStoreAdminLink.warehouse_group_id == WarehouseGroupLink.warehouse_group_id)
            .join(WarehouseGroup, WarehouseGroup.id == WarehouseGroupLink.warehouse_group_id)
            .where(
                WarehouseStoreAdminLink.user_id == current_user.id,
                Warehouse.id.not_in(deny_warehouses_subquery)
            )
            .distinct()
        )


        warehouses = session.exec(statement).all()
        print("warehouses",warehouses)

        
        access_policy_order = {
            "deny": 0,
            "view": 1,
            "edit": 2,
            "contribute": 3,
            "manage": 4
        }
        warehouse_list=[]

        for warehouse in warehouses:
            # Get all groups for this warehouse
            group_ids = session.exec(
                select(WarehouseGroup.id, WarehouseGroup.access_policy)
                .join(WarehouseGroupLink, WarehouseGroup.id == WarehouseGroupLink.warehouse_group_id)
                .join(WarehouseStoreAdminLink, WarehouseGroup.id == WarehouseStoreAdminLink.warehouse_group_id)
                .where(
                    WarehouseGroupLink.warehouse_id == warehouse.id,
                    WarehouseStoreAdminLink.user_id == current_user.id,
                    WarehouseGroup.access_policy != "deny"  # skip deny
                )
            ).all()

            if not group_ids:
                continue  # skip if no valid access

            # Find the lowest access policy
            min_policy = min(group_ids, key=lambda g: access_policy_order[g.access_policy]).access_policy


            warehouse_list.append({
                "id": warehouse.id,
                "warehouse_name": warehouse.warehouse_name,
                "organization": warehouse.organization_id,
                "landmark": warehouse.landmark,
                "min_access_policy": min_policy,
            })
       

        return warehouse_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))   
    
@wr.get(endpoint['get_by_id'] + "/{id}")
async def get_warehouse(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,
):
    try:
        if not check_permission(
            session, "Read", role_modules['get'],current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
       
        warehouse = session.exec(select(Warehouse).where(Warehouse.id == id)).first()
        if not warehouse:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        
        location_db = session.exec(select(Geolocation).where(Geolocation.id == warehouse.location_id)).first()
        location_str = f"({location_db.latitude},{location_db.longitude})"
  
        return {
            "id": warehouse.id,
            "warehouse_name": warehouse.warehouse_name,
            "organization": warehouse.organization_id,
            "address": warehouse.address_id,
            "landmark": warehouse.landmark,
            "latitude":location_db.latitude,
            "longitude": location_db.longitude
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    

@wr.put(endpoint['update'])
async def update_warehouse(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    valid: TemplateView
  
):

    try:
        if not check_permission(
            session, "Update",role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
       
        existing_warehouse = session.exec(select(Warehouse).where(Warehouse.id == valid.id)).first()

        if not existing_warehouse:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse does not exsit",
        )

        existing_geolocation = session.exec(
            select(Geolocation).where(
                Geolocation.latitude == valid.latitude,
                Geolocation.longitude == valid.longitude
            )
        ).first()

        location_id : int
        if existing_geolocation:
            location_id = existing_geolocation.id 
       
        else:
            location_db = Geolocation(
                id=None,
                latitude=valid.latitude,
                longitude=valid.longitude,
            )
            session.add(location_db)
            session.commit()
            session.refresh(location_db)
            location_id = location_db.id

        existing_warehouse.warehouse_name = valid.warehouse_name
        existing_warehouse.organization_id = valid.organization
        existing_warehouse.address_id = valid.address
        existing_warehouse.landmark = valid.landmark
        existing_warehouse.location_id = location_id

        
        session.add(existing_warehouse)
        session.commit()
        session.refresh(existing_warehouse)
        
        return existing_warehouse.id
    except Exception as e:
        
        raise HTTPException(status_code=400, detail=str(e)) 

@wr.delete(endpoint['delete']+ "/{id}")
async def delete_warehouse(
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
       
    
        warehouse = session.get(Warehouse, id)

        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Warehouse not found",
            )
        
        warehouse_group_links = session.exec(
            select(WarehouseGroupLink)
            .where(WarehouseGroupLink.warehouse_id == id)
        ).all()
        print("WGL", warehouse_group_links)

        for link in warehouse_group_links:
            # Check how many warehouses this group is linked to
            # group_links_count = session.exec(
            #     select(WarehouseGroupLink).where(WarehouseGroupLink.warehouse_group_id == link.warehouse_group_id)
            # ).all()

            # if len(group_links_count) == 1:
            #     # This group is linked only to the current warehouse, safe to delete its admin links
            #     store_admin_links = session.exec(
            #         select(WarehouseStoreAdminLink).where(
            #             WarehouseStoreAdminLink.warehouse_group_id == link.warehouse_group_id
            #         )
            #     ).all()
            #     print("SAL (to delete):", store_admin_links)
            #     for admin in store_admin_links:

            #         session.delete(admin)
            #         session.commit()

            # Delete the warehouse group link (safe to always delete)
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
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 

