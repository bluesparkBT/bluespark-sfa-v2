from typing import Annotated, List, Dict, Any, Optional, Union
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from utils.model_converter_util import get_html_types
from models.Account import User, ScopeGroup,ScopeGroupLink, Organization, Role
from utils.util_functions import validate_name
from models.viewModel.OrderView import OrderView as TemplateView #Update this
from utils.auth_util import get_current_user, check_permission, check_permission_and_scope
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_order_id_and_name, fetch_organization_id_and_name, fetch_id_and_name
import traceback

#Update router name
OrderProvider = c = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "order" #Update this
db_model = Order #Update this

endpoint = {
    "get": f"/get-{endpoint_name}s",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",
    "update": f"/update-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}

#Update role_modules
role_modules = {   
    "get": ["Administrative", "Order"],
    "get_form": ["Administrative", "Order"],
    "create": ["Administrative", "Order"],
    "update": ["Administrative", "Order"],
    "delete": ["Administrative", "Order"],
}


#CRUD
@c.get(endpoint['get'])
def get_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:  
        orgs_in_scope = check_permission_and_scope(session, "Read", role_modules['get'], current_user)
        
        entries_list = session.exec(
            select(db_model).where(db_model.organization.in_(orgs_in_scope["organization_ids"]))
        ).all()
        
        #Business Logic

        return entries_list

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
 
@c.get(endpoint['get_by_id'] + "/{id}")
def get_template(
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
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        entry = session.exec(
            select(db_model).where(db_model.organization.in_(organization_ids), db_model.id == id)

        ).first()

        if not entry:
            raise HTTPException(status_code=404, detail= f"{endpoint_name} not found")
        
        #Business Logic
        return entry
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

#Create entry template 
@c.post(endpoint['create'])
def create_template(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    valid: TemplateView,
):
    try:
        if not check_permission(
            session, "Create", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You do not have the required privilege"
            )
        
        # Create a new order entry from validated input
        # new_entry = db_model.model_validate(valid)        
        new_entry = db_model(
            employee = current_user.id,
            sales = valid.sales.id,
            point_of_sale = valid.point_of_sale.id,
            date = valid.date, # Update this
            expected_date = valid.expected_date, 
            remark = valid.remark,
            status = valid.status,
            total = valid.total,
            total_quantity = valid.total_quantity)
        
        session.add(new_entry)
        session.commit()
        session.refresh(new_entry)

        return new_entry

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
 
# update a single entry by ID template
@c.put(endpoint['update'])
def update_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    valid: TemplateView,
):
    try:
        # Check permission
        if not check_permission(
            session, "Update", role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        selected_entry = session.exec(
            select(db_model).where(db_model.organization.in_(organization_ids), db_model.id == valid.id)
        ).first()

        if not selected_entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")
        
        if valid.organization == organization_ids:
            selected_entry.organization = valid.organization
        else:
            {"message": "invalid input select your own organization id"}    
 
        # Commit the changes and refresh the object
        selected_entry.expected_date = valid.expected_date
        selected_entry.remark = valid.remark
        selected_entry.status = valid.status
   
        session.add(valid)
        session.commit()
        session.refresh(valid)

        return {"message": f"{endpoint_name} Updated successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

# Delete by ID Template
@c.delete(endpoint['delete']+ "/{id}")
def delete_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int
) :
    try:
        # Check permission
        if not check_permission(
            session, "Delete", role_modules['delete'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        selected_entry = session.exec(
            select(db_model).where(db_model.organization.in_(organization_ids), db_model.id == id)
        ).first()

        if not selected_entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

        # Delete order after validation
        session.delete(selected_entry)
        session.commit()

        return {"message": f"{endpoint_name} deleted successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
