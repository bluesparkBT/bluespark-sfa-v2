from typing import Annotated, List, Dict, Any, Optional, Union
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from utils.model_converter_util import get_html_types
from models.Account import User, ScopeGroup,ScopeGroupLink, Organization, Role
from utils.util_functions import validate_name
from models.viewModel.AccountsView import UserAccountView as TemplateView #Update this
from utils.auth_util import get_current_user, check_permission, check_permission_and_scope
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_category_id_and_name, fetch_organization_id_and_name, fetch_id_and_name
import traceback


endpoint_name = "superadmin" #Update this
db_model = User #Update this

endpoint = {
    "get": f"/get-{endpoint_name}",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",
    "update": f"/update-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}

#Update role_modules
role_modules = {   
    "get": ["Service Provider", "Tenant Management"],
    "get_form": ["Service Provider", "Tenant Management"],
    "create": ["Service Provider", "Tenant Management"],
    "update": ["Service Provider", "Tenant Management"],
    "delete": ["Service Provider"],
}

#Update router name
ServiceProvider = c = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

UserDep = Annotated[dict, Depends(get_current_user)]


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
            select(db_model).where(db_model.organization_id.in_(orgs_in_scope["organization_ids"]))
        ).all()

        return entries_list

    except Exception as e:
        traceback.print_exc()
 
@c.get(endpoint['get_by_id'] + "/{id}")
def get_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int,
    # valid: TemplateView,
):
    try:
        orgs_in_scope = check_permission_and_scope(session, "Read", role_modules['get'], current_user)

        entry = session.exec(
            select(db_model).where(db_model.organization_id.in_(organization_ids), db_model.id == id)
        ).first()

        if not entry:
            raise HTTPException(status_code=404, detail="Category not found")
        

        return entry
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@c.post(endpoint['create'])
def create_template(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    valid: TemplateView,
):
    try:
        

        # Create a new category entry from validated input

        new_entry = db_model.model_validate(valid)        
        
        session.add(new_entry)
        session.commit()
        session.refresh(new_entry)

        return new_entry

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
 
# update a single category by ID
@c.post(endpoint['update'])
def update_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    valid: TemplateView,
):
    try:
        # Check permission
        orgs_in_scope = check_permission_and_scope(session, "Update", role_modules['update'], current_user)

        selected_entry = session.exec(
            select(db_model).where(db_model.organization_id.in_(organization_ids), db_model.id == valid.id)
        ).first()

        if not selected_entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")
        
        if valid.organization == organization_ids:
            selected_entry.organization_id = valid.organization
        else:
            {"message": "invalid input select your own organization id"}    
 
        # Commit the changes and refresh the object
        session.add(valid)
        session.commit()
        session.refresh(valid)

        return {"message": f"{endpoint_name} Updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Delete a category by ID
@c.delete(endpoint['delete']+ "/{id}")
def delete_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int
) :
    try:
        # Check permission
        orgs_in_scope = check_permission_and_scope(session, "Delete", role_modules['delete'], current_user)

        selected_entry = session.exec(
            select(db_model).where(db_model.organization_id.in_(organization_ids), db_model.id == id)
        ).first()

        if not selected_entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

    
        # Delete category after validation
        session.delete(selected_entry)
        session.commit()

        return {"message": f"{endpoint_name} deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
