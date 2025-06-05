from typing import Annotated, Any, Dict, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Body, Path, status
from sqlmodel import Session, select
import traceback
from db import SECRET_KEY, get_session
from models.Warehouse import WarehouseGroup, WarehouseGroupLink, WarehouseStoreAdminLink
from models.Account import AccessPolicy, Organization
from utils.auth_util import get_current_user, check_permission
from utils.model_converter_util import get_html_types
from utils.util_functions import parse_enum
from utils.form_db_fetch import fetch_admin_warehouse_id_and_name
from models.viewModel.WarehouseView import WarehouseGroup as TemplateView
from utils.get_hierarchy import get_organization_ids_by_scope_group

WarehouseGroupRouter = wr = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "warehouse-group"
db_model = WarehouseGroup

endpoint = {
    "get": f"/get-{endpoint_name}s",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
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
        existing_entry = session.exec(select(db_model).where(db_model.name == valid.name)).first()

        if existing_entry is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                 detail= f"{endpoint_name} already registered",
        )
        organization = session.exec(select(Organization).where(Organization.tenant_hashed == tenant)).first()
        
        warehouse_group = WarehouseGroup(
            id = None,
            name = valid.name,
            access_policy=parse_enum(AccessPolicy,valid.access_policy,"access policy"),
            organization_id=organization.id
        )
        
        session.add(warehouse_group)
        session.commit()
        session.refresh(warehouse_group)

        for warehouse in valid.warehouses:
            warehouse_link = WarehouseGroupLink(
                id=None,
                warehouse_id = warehouse,
                warehouse_group_id = warehouse_group.id
            )
            session.add(warehouse_link)
            session.commit()
            session.refresh(warehouse_link)
        return {"message": "Warehouse Group created successfully."}
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
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        
        warehouse_groups = session.exec(
            select(db_model).where(db_model.organization_id.in_(organization_ids))
        ).all()

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
    
@wr.get(endpoint['get_by_id'] + "/{id}")
async def get_warehouse_group(
    session: SessionDep,
    id: int,
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
        warehouse_group = session.exec(select(db_model).where(WarehouseGroup.id == id)).first()
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
    
# @wr.get("/get-my-warehouse-group/{id}")
# async def get_my_warehouse_group(
#     session: SessionDep,
#     id: int,
#     current_user: UserDep,
#     tenant: str,
# ):
#     try:
#         if not check_permission(
#             session, "Read",role_modules['get'], current_user
#             ):
#             raise HTTPException(
#                 status_code=403, detail="You Do not have the required privilege"
#             )
#         warehouse_groups = session.exec(
#             select(WarehouseGroup)
#             .join(WarehouseStoreAdminLink, WarehouseStoreAdminLink.warehouse_group_id == WarehouseGroup.id)
#             .join(WarehouseGroupLink, WarehouseGroupLink.warehouse_group_id == WarehouseGroup.id)
#             .where(
#                 WarehouseStoreAdminLink.user_id == current_user.id,
#                 WarehouseGroupLink.warehouse_id == id
#             )
#         ).all()
#         if not warehouse_groups:
#             raise HTTPException(status_code=404, detail="Warehouse Group not found")
        
  
#         warehouse_group_list = []

#         for warehouse_group in warehouse_groups:
#             warehouse_group_list.append({
#                 "id": warehouse_group.id,
#                 "name": warehouse_group.name,
#                 "access_policy": warehouse_group.access_policy,
#                 "warehouses": [warehouse.warehouse_name for warehouse in warehouse_group.warehouses],
#             })
        

#         return warehouse_group_list
#     except Exception as e:
#         traceback.print_exc()
#         raise HTTPException(status_code=400, detail=str(e))
    

@wr.put(endpoint['update'])
async def udpate_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    valid: TemplateView
  
):

    try:
        if not check_permission(
            session, "Update", role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        existing_warehouse_group = session.exec(select(db_model).where(db_model.id == valid.id)).first()

        if not existing_warehouse_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse Group does not exsit",
        )
       

        existing_warehouse_group.name = valid.name
        existing_warehouse_group.access_policy = valid.access_policy
     
        session.add(existing_warehouse_group)
        session.commit()
        session.refresh(existing_warehouse_group)

         # Step 1: Get existing warehouse for the warehouse groups
        existing_warehouses = session.exec(
            select(WarehouseGroupLink.warehouse_id).where(WarehouseGroupLink.warehouse_group_id == valid.id)
        ).all()
        print("step 1")

        existing_warehouse_ids = set(existing_warehouses)
        new_warehouse_ids = set(valid.warehouses)

        # Step 2: Find which ones to add
        to_add = new_warehouse_ids - existing_warehouse_ids
        new_links = [
            WarehouseGroupLink(
                warehouse_id=warehouse_id,
                warehouse_group_id = valid.id
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
                .where(WarehouseGroupLink.warehouse_group_id == valid.id)
                .where(WarehouseGroupLink.warehouse_id.in_(to_remove))
            ):
                session.delete(link)
                session.commit()
        
        return {"message": "Warehouse group updated successfully"}
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
            session, "Delete", role_modules['delete'], current_user
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