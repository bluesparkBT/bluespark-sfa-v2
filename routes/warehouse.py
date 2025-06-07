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


WarehouseRouter = wr = APIRouter()\
    
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

request_to_log_type_map = {
    RequestType.stock_out: LogType.stock_out,
    RequestType.transfer: LogType.transfer,
    RequestType.return_defect: LogType.return_defect,
    RequestType.return_normal: LogType.return_normal,
}

@wr.get("/warehouse-group-form")
async def form_warehouse_group(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        if not check_permission(
            session, "Update", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        warehouse_data = {
                "id": "",
                "name": "",
                "access_policy":{i.value: i.value for i in AccessPolicy},
                "warehouses": fetch_admin_warehouse_id_and_name(session, current_user),
            }
            
        return {"data": warehouse_data, "html_types": get_html_types("warehouse-group")}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.post("/create-warehouse-group/")
async def create_warehouse_group(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    name: str = Body(...),
    access_policy: str = Body(...),
    warehouses: List[int] = Body(...),
  
):
    try:
        if not check_permission(
            session, "Create", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        existing_warehouse_group = session.exec(select(WarehouseGroup).where(WarehouseGroup.name == name)).first()

        if existing_warehouse_group is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse Group name already registered",
        )
        organization = session.exec(select(Organization).where(Organization.tenant_hashed == tenant)).first()
        
        warehouse_group = WarehouseGroup(
            id = None,
            name = name,
            access_policy=parse_enum(AccessPolicy,access_policy,"access policy"),
            organization_id=organization.id
        )
        
        session.add(warehouse_group)
        session.commit()
        session.refresh(warehouse_group)

        for warehouse in warehouses:
            warehouse_link = WarehouseGroupLink(
                id=None,
                warehouse_id = warehouse,
                warehouse_group_id = warehouse_group.id
            )
            session.add(warehouse_link)
            session.commit()
            session.refresh(warehouse_link)
        return {"message": "Warehouse Group "+warehouse_group.name+" added successfully."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.get("/get-warehouse-groups/")
async def get_warehouse_groups(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

):
  
    try:
        if not check_permission(
            session, "Read", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        warehouse_groups = session.exec(select(WarehouseGroup)).all()

        warehouse_group_list = []

        for warehouse_group in warehouse_groups:
            warehouse_group_list.append({
                "id": warehouse_group.id,
                "name": warehouse_group.name,
                "access_policy": warehouse_group.access_policy,
                "warehouses": [warehouse.warehouse_name for warehouse in warehouse_group.warehouses],
            })
        

        return warehouse_group_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))   
    
@wr.get("/get-warehouse-group/{id}")
async def get_warehouse_group(
    session: SessionDep,
    id: int,
    current_user: UserDep,
    tenant: str,
):
    try:
        if not check_permission(
            session, "Read", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        warehouse_group = session.exec(select(WarehouseGroup).where(WarehouseGroup.id == id)).first()
        if not warehouse_group:
            raise HTTPException(status_code=404, detail="Warehouse Group not found")
        
  
        return {
            "id": warehouse_group.id,
            "name": warehouse_group.name,
            "access_policy": warehouse_group.access_policy,
            "warehouses": [warehouse.id for warehouse in warehouse_group.warehouses],
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.get("/get-my-warehouse-group/{id}")
async def get_my_warehouse_group(
    session: SessionDep,
    id: int,
    current_user: UserDep,
    tenant: str,
):
    try:
        if not check_permission(
            session, "Read", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        warehouse_groups = session.exec(
            select(WarehouseGroup)
            .join(WarehouseStoreAdminLink, WarehouseStoreAdminLink.warehouse_group_id == WarehouseGroup.id)
            .join(WarehouseGroupLink, WarehouseGroupLink.warehouse_group_id == WarehouseGroup.id)
            .where(
                WarehouseStoreAdminLink.user_id == current_user.id,
                WarehouseGroupLink.warehouse_id == id
            )
        ).all()
        if not warehouse_groups:
            raise HTTPException(status_code=404, detail="Warehouse Group not found")
        
  
        warehouse_group_list = []

        for warehouse_group in warehouse_groups:
            warehouse_group_list.append({
                "id": warehouse_group.id,
                "name": warehouse_group.name,
                "access_policy": warehouse_group.access_policy,
                "warehouses": [warehouse.warehouse_name for warehouse in warehouse_group.warehouses],
            })
        

        return warehouse_group_list
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    

@wr.put("/update-warehouse-group/")
async def update_warehouse_group(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int = Body(...),
    name: str = Body(...),
    access_policy: str = Body(...),
    warehouses: List[int] = Body(...),
  
):

    try:
        if not check_permission(
            session, "Update", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        existing_warehouse_group = session.exec(select(WarehouseGroup).where(WarehouseGroup.id == id)).first()

        if not existing_warehouse_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse Group does not exsit",
        )
       

        existing_warehouse_group.name = name
        existing_warehouse_group.access_policy = access_policy
     
        session.add(existing_warehouse_group)
        session.commit()
        session.refresh(existing_warehouse_group)

         # Step 1: Get existing warehouse for the warehouse groups
        existing_warehouses = session.exec(
            select(WarehouseGroupLink.warehouse_id).where(WarehouseGroupLink.warehouse_group_id == id)
        ).all()
        print("step 1")

        existing_warehouse_ids = set(existing_warehouses)
        new_warehouse_ids = set(warehouses)

        # Step 2: Find which ones to add
        to_add = new_warehouse_ids - existing_warehouse_ids
        new_links = [
            WarehouseGroupLink(
                warehouse_id=warehouse_id,
                warehouse_group_id = id
            )
            for warehouse_id in to_add
        ]
        print("stpe2")

        session.add_all(new_links)
        session.commit()

        # Step 3: Optionally, find which ones to remove
        to_remove = existing_warehouse_ids - new_warehouse_ids
        if to_remove:
         
            for link in session.exec(
                select(WarehouseGroupLink)
                .where(WarehouseGroupLink.warehouse_group_id == id)
                .where(WarehouseGroupLink.warehouse_id.in_(to_remove))
            ):
                session.delete(link)
                session.commit()
        
        return {"message": "Warehouse group updated successfully"}
    except Exception as e:
        
        raise HTTPException(status_code=400, detail=str(e)) 

@wr.delete("/delete-warehouse-group/{id}")
async def delete_warehouse_group(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,    
):
  
    try:
        if not check_permission(
            session, "Delete", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
    
        warehouse_group = session.get(WarehouseGroup, id)

        if not warehouse_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Warehouse Grop not found",
            )
        
        store_admin_links = session.exec(
            select(WarehouseStoreAdminLink).where(WarehouseStoreAdminLink.warehouse_group_id == id)
        ).all()

        for link in store_admin_links:
            session.delete(link)
            session.commit()

        warehouse_group_links = session.exec(
            select(WarehouseGroupLink).where(WarehouseGroupLink.warehouse_group_id == id)
        ).all()

        for link in warehouse_group_links:
            session.delete(link)
            session.commit()


       
        session.delete(warehouse_group)
        session.commit()

        return {"message": "Warehouse group deleted successfully"}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 
    
#starts here
    
@wr.get("/store-admin-form")
async def form_store_admin(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        if not check_permission(
            session, "Update", "Administrative", current_user
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
    
@wr.post("/assign-store-admin/")
async def assign_store_admin(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    warehouse_group: int = Body(...),
    store_admins: List[int] = Body(...),
  
):
    try:
        if not check_permission(
            session, "Create", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        existing_warehouse_storeadmin = session.exec(select(WarehouseStoreAdminLink).where(WarehouseStoreAdminLink.warehouse_group_id == warehouse_group)).first()

        if existing_warehouse_storeadmin is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse Group Store admin link already exists",
        )
        
       

        for store_admin in store_admins:
            link = WarehouseStoreAdminLink(
                id=None,
                user_id = store_admin,
                warehouse_group_id = warehouse_group,
            )
            session.add(link)
            session.commit()
            session.refresh(link)
        return {"message": "Store admin added successfully."}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.get("/get-store-admins/")
async def get_store_admins(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

):
  
    try:
        if not check_permission(
            session, "Read", "Administrative", current_user
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
                "store_admins": [store_admin.fullname for store_admin in warehouse_group.store_admins],
            })
        

        return store_admin_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))   
    
@wr.get("/get-store-admin/{id}")
async def get_store_admin(
    session: SessionDep,
    id: int,
    current_user: UserDep,
    tenant: str,
):
    try:
        if not check_permission(
            session, "Read", "Administrative", current_user
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

@wr.get("/store-admin-update-form")
async def form_update_store_admin(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        if not check_permission(
            session, "Update", "Administrative", current_user
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

@wr.put("/update-store-admin/")
async def update_store_admin(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    warehouse_group: int = Body(...),
    store_admins: List[int] = Body(...)
  
):

    try:
        if not check_permission(
            session, "Update", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
 
        existing_warehouse_group = session.exec(select(WarehouseGroup).where(WarehouseGroup.id == warehouse_group)).first()

        if not existing_warehouse_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse Group does not exsit",
        )
       
         # Step 1: Get existing store admins for the warehouse groups
        existing_store_admins = session.exec(
            select(WarehouseStoreAdminLink.user_id).where(WarehouseStoreAdminLink.warehouse_group_id == warehouse_group)
        ).all()
        print("step 1")
    

        existing_storeadmin_ids = set(existing_store_admins)
        new_storeadmin_ids = set(store_admins)

        # Step 2: Find which ones to add
        to_add = new_storeadmin_ids - existing_storeadmin_ids
        new_links = [
            WarehouseStoreAdminLink(
                user_id=user_id,
                warehouse_group_id = warehouse_group
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
            .where(WarehouseStoreAdminLink.warehouse_group_id == warehouse_group)
            .where(WarehouseStoreAdminLink.user_id.in_(to_remove))
            ).all()

            # Delete them
            for link in links:
                session.delete(link)
                session.commit()
        
        return {"message": "Store admin updated successfully"}
    except Exception as e:
        
        raise HTTPException(status_code=400, detail=str(e)) 

@wr.delete("/delete-store-admin/{id}")
async def delete_store_admin(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,    
):
  
    try:
        if not check_permission(
            session, "Delete", "Administrative", current_user
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
    
    #ends here


@wr.get("/warehouse-form")
async def form_warehouse(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        if not check_permission(
            session, "Update", "Inventory Management", current_user
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
    
@wr.post("/create-warehouse/")
async def create_warehouse(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    warehouse_name: str = Body(...),
    organization: int = Body(...),
    address: int | str = Body(...),
    landmark: str | None = Body(...),
    latitude: float = Body(...),
    longitude: float = Body(...)
  
):
    try:
        if not check_permission(
            session, "Create", "Inventory Management", current_user
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
      
        location_db = Geolocation(
            id = None,
            latitude = latitude,
            longitude= longitude,
        )
        session.add(location_db)
        session.commit()
        session.refresh(location_db)


        
        warehouse = Warehouse(
            id = None,
            warehouse_name = warehouse_name,
            organization_id = organization,
            address_id = None if address == "" else address,
            landmark = landmark,
            location_id = location_db.id,
        )
        
        session.add(warehouse)
        session.commit()
        session.refresh(warehouse)

        # add the created warehouse to the warehouse group assigned to the system admin
        organization = session.exec(select(Organization).where(Organization.tenant_hashed == tenant)).first()
        warehouse_group = session.exec(
            select(WarehouseGroup).where(
                (WarehouseGroup.organization_id == organization.id) &
                (WarehouseGroup.name == f"{organization.organization_name} Admin Warehouse Group")
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

    

@wr.get("/get-warehouses/")
async def get_warehouses(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

):
  
    try:
     
        if not check_permission(
            session, "Read", "Inventory Management", current_user
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
                "organization": warehouse.organization.organization_name,
                "landmark": warehouse.landmark,
                "min_access_policy": min_policy,
            })
       

        return warehouse_list

    except Exception as e:
        traceback.print_exc()
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
            session, "Read", "Inventory Management", current_user
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
    

@wr.put("/update-warehouse/")
async def update_warehouse(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int = Body(...),
    warehouse_name: str = Body(...),
    organization: int = Body(...),
    address: int | str = Body(...),
    landmark: str | None = Body(...),
    latitude: float = Body(...),
    longitude: float = Body(...)
  
):

    try:
        if not check_permission(
            session, "Update", "Inventory Management", current_user
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

        existing_geolocation = session.exec(
            select(Geolocation).where(
                Geolocation.latitude == latitude,
                Geolocation.longitude == longitude
            )
        ).first()

        location_id : int
        if existing_geolocation:
            location_id = existing_geolocation.id 
       
        else:
            location_db = Geolocation(
                id=None,
                latitude=latitude,
                longitude=longitude,
            )
            session.add(location_db)
            session.commit()
            session.refresh(location_db)
            location_id = location_db.id

        existing_warehouse.warehouse_name = warehouse_name
        existing_warehouse.organization_id = organization
        existing_warehouse.address_id = None if address == "" else address
        existing_warehouse.landmark = landmark
        existing_warehouse.location_id = location_id

        
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
            session, "Delete", "Inventory Management", current_user
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
    
@wr.get("/stock-form")
async def form_stock(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        if not check_permission(
            session, "Update", "Inventory Management", current_user
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
        traceback.print_exc()
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
            session, "Create", "Inventory Management", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        if not check_warehouse_permission(
            session, "Create", warehouse,current_user
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
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.get("/get-stocks/")
async def get_stocks(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

):
  
    try:
        if not check_permission(
            session, "Read", "Inventory Management", current_user
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
        traceback.print_exc()
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
            session, "Read", "Inventory Management", current_user
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
            "warehouse": stock.warehouse_id,
            "product": stock.product_id,
            "category": stock.category_id,
            "sub_category": stock.subcategory_id,
            "quantity": stock.quantity,
            "stock_type": stock.stock_type,
        }
    except Exception as e:
        traceback.print_exc()
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
            session, "Update", "Inventory Management", current_user
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
        if not check_warehouse_permission(
            session, "Update", warehouse,current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
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
        traceback.print_exc()
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
            session, "Delete", "Inventory Management", current_user
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
        traceback.print_exc()
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
            session, "Read", "Inventory Management", current_user
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
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.get("/warehouse-stop-form")
async def form_warehouse_stop(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        if not check_permission(
            session, "Update", "Inventory Management", current_user
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
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.post("/create-warehouse-stop/")
async def create_warehouse_stop(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    request_type: str = Body(...),
    vehicle: int|str = Body(...),
    stock: int = Body(...),
    quantity: int = Body(...),
    stock_type: str = Body(...)
):

    try:
        if not check_permission(
            session, "Create", "Inventory Management", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        stock_data = session.exec(select(Stock).where(Stock.id == stock)).first()
        if not check_warehouse_permission(
            session, "Create",stock_data.warehouse_id,current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

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
            vehicle_id = None if vehicle=="" else vehicle,
            stock_id=stock,
            quantity = quantity,
            stock_type=parse_enum(StockType, stock_type,"Stock Type")             
        )
        
        
        session.add(warehouse_stop)
        session.commit()
        session.refresh(warehouse_stop)
        
        return {"message": "Warehouse stop created successfully"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@wr.get("/get-warehouse-stops/")
async def get_warehouse_stops(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

):
  
    try:
        if not check_permission(
            session, "Read", "Inventory Management", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
    
        warehouse_stop_list = []

      
        # Step 1: find warehouse IDs the current user is linked to via a deny access policy
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
            for stock in warehouse.stocks:
                st = session.exec(select(Stock).where(Stock.id == stock.id)).first()
                print("stock", st)
                for stop in st.warehouse_stops:
                    print("stop", stop)
                    warehouse_stop_list.append({
                        "id": stop.id,
                        "warehouse_name": stop.stock.warehouse.warehouse_name,
                        "stock": stop.stock.product.name,
                        "stock_type": stop.stock_type,
                        "quantity": stop.quantity,
                        "vehicle": stop.vehicle.name if stop.vehicle else "",
                        "requester": stop.requester.fullname,
                        "request_status": stop.request_status,
                        "request_type": stop.request_type,
                        "request_date": format_date_for_input(stop.request_date),
                        "approver": stop.approver.fullname if stop.approver_id is not None else "",
                        "approved_date": format_date_for_input(stop.approve_date),
                        "confirmed_date": stop.confirm_date,
                        "confirmed": stop.confirmed,
                        "isRequest": False,
                        "min_access_policy": min_policy
                    })
    
        return warehouse_stop_list

    except Exception as e:
        traceback.print_exc()
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
            session, "Read", "Inventory Management", current_user
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
        traceback.print_exc()
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
            session, "Read", "Inventory Management", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        statement = (
            select(WarehouseStop)
            .join(Stock, WarehouseStop.stock_id == Stock.id)
            .join(Warehouse, Stock.warehouse_id == Warehouse.id)
            .join(WarehouseGroupLink, WarehouseGroupLink.warehouse_id == Warehouse.id)
            .join(WarehouseStoreAdminLink, WarehouseStoreAdminLink.warehouse_group_id == WarehouseGroupLink.warehouse_group_id)
            .where(WarehouseStoreAdminLink.user_id == current_user.id)
            .where(WarehouseStop.request_status == parse_enum(RequestStatus,status, "Request Status"))).distinct()
        
        warehouse_stops = session.exec(statement).all()

        warehouse_stop_list = []

        for stop in warehouse_stops:
            warehouse_stop_list.append({
                "id": stop.id,
                "warehouse_name": stop.stock.warehouse.warehouse_name,
                "stock": stop.stock.product.name,
                "stock_type": stop.stock_type,
                "quantity": stop.quantity,
                "vehicle": stop.vehicle.name if stop.vehicle else "",
                "requester": stop.requester.fullname,
                "request_status": stop.request_status,
                "request_type": stop.request_type,
                "request_date": format_date_for_input(stop.request_date),
                "approver": stop.approver.fullname if stop.approver_id is not None else "",
                "approved_date": format_date_for_input(stop.approve_date),
                "confirmed_date": stop.confirm_date,
                "confirmed": stop.confirmed,
                "isRequest": False
            })
        

        return warehouse_stop_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 
    
@wr.get("/get-warehouse-stops/request/")
async def get_my_warehouse_stop_requests(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

):
  
    try:
        if not check_permission(
            session, "Read", "Inventory Management", current_user
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
                "vehicle": stop.vehicle.name if stop.vehicle else "",
                "requester": stop.requester.fullname,
                "request_status": stop.request_status,
                "request_type": stop.request_type,
                "request_date": format_date_for_input(stop.request_date),
                "approver": stop.approver.fullname if stop.approver_id is not None else "",
                "approved_date": format_date_for_input(stop.approve_date),
                "confirmed_date": format_date_for_input(stop.confirm_date),
                "confirmed": stop.confirmed,
                "isRequest": True
            })
        

        return warehouse_stop_list

    except Exception as e:
        traceback.print_exc()
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
            session, "Read", "Inventory Management", current_user
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
        traceback.print_exc()
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
            session, "Read", "Inventory Management", current_user
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
        traceback.print_exc()
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
            session, "Read", "Inventory Management", current_user
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
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 
    
@wr.put("/update-warehouse-stop/")
async def update_warehouse_stop(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int = Body(...),
    request_type: str = Body(...),
    vehicle: int|str= Body(...),
    stock: int = Body(...),
    quantity: int = Body(...),
    stock_type: str = Body(...)
):

    try:
        if not check_permission(
            session, "Create", "Inventory Management", current_user
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
        warehouse_stop.vehicle_id = None if vehicle=="" else vehicle
        warehouse_stop.stock_id=stock
        warehouse_stop.quantity = quantity
        warehouse_stop.stock_type=parse_enum(StockType, stock_type,"Stock Type")             
      
        session.add(warehouse_stop)
        session.commit()
        session.refresh(warehouse_stop)
        
        return {"message": "Warehouse stop updated successfully"}
    except Exception as e:
        traceback.print_exc()
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
            session, "Delete", "Inventory Management", current_user
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