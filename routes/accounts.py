from typing import Annotated, List, Dict, Any, Optional, Union
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from utils.model_converter_util import get_html_types
from models.Account import User, ScopeGroup,ScopeGroupLink 
from utils.util_functions import validate_name
from models.viewModel.AccountsView import UserAccountView as TemplateView
from models.Account import Organization
from utils.auth_util import (get_current_user, 
                             check_permission, 
                             check_permission_and_scope,
                            generate_random_password,
                            get_password_hash,add_organization_path,
                            verify_password
                            )
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_category_id_and_name, fetch_organization_id_and_name, fetch_id_and_name

import traceback


endpoint_name = "account"

db_model = User

endpoint = {
    "get": f"/get-{endpoint_name}",
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

AccountRouter = c = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

UserDep = Annotated[dict, Depends(get_current_user)]


#Authentication Related
@c.post("/login/")
def login(
    session: SessionDep,
    tenant: str,
    username: str = Body(...),
    password: str = Body(...)
):
    try:
        current_tenant = session.exec(select(Organization).where(Organization.tenant_hashed == tenant)).first()
        if not current_tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        db_username = add_organization_path(username, current_tenant.organization_name)
        user = session.exec(
            select(User).where(User.username == db_username)
        ).first()
        if not user or not verify_password(password + db_username, user.hashedPassword):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
        access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        token = create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "organization": user.organization_id,
                },
            expires_delta = access_token_expires,
        )
        
        return {"access_token": token}
    
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}
        
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
        if not check_permission(
            session, "Read",[ "Category", "Administrative"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        # Fetch categories based on organization IDs
        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        entry = session.exec(
            select(db_model).where(db_model.organization_id.in_(organization_ids), db_model.id == id)
        ).first()

        if not entry:
            raise HTTPException(status_code=404, detail="Category not found")
        

        return entry
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@c.get(endpoint['get_form'])
def get_template_form(
    tenant: str,
    session: SessionDep,
    current_user: UserDep,
) :
    """   Retrieves the form structure for creating a new category.
    """
    try:
        # Check permission
        if not check_permission(
            session, "Create",role_modules['get_form'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )   

          # This will display a list of category names

        form_structure = {
            "id": "",
            "name": "",
            "code": "",
            "description": "",
            "parent_category": fetch_category_id_and_name(session, current_user),
            "organization": fetch_organization_id_and_name(session, current_user),
        } 

        return {"data": form_structure, "html_types": get_html_types("category")}

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
        
        if not check_permission(
            session, "Create", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        # Create a new category entry from validated input
        new_category = db_model.model_validate(valid)
        session.add(new_category)
        session.commit()
        session.refresh(new_category)

        return new_category

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
        if not check_permission(
            session, "Update",role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        # Fetch categories based on organization IDs
        organization_ids = get_organization_ids_by_scope_group(session, current_user)

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
        if not check_permission(
            session, "Delete",role_modules['delete'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        # Fetch categories based on organization IDs
        organization_ids = get_organization_ids_by_scope_group(session, current_user)

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
