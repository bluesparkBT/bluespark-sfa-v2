from typing import Annotated, List, Dict, Any, Optional, Union
from datetime import timedelta
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from utils.model_converter_util import get_html_types
from models.Account import User, ScopeGroup,ScopeGroupLink 
from utils.util_functions import validate_name
from models.viewModel.AccountsView import ScopeGroupView as TemplateView, UpdateScopeGroupView as UpdateTemplateView
from models.Account import User, ScopeGroup, ScopeGroupLink, Organization, Gender, Scope, Role, AccessPolicy, IdType
from utils.util_functions import validate_name, validate_email, validate_phone_number, parse_datetime_field, format_date_for_input, parse_enum
from utils.auth_util import get_current_user, check_permission, check_permission_and_scope, add_organization_path, verify_password, get_password_hash, create_access_token, generate_random_password
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_category_id_and_name, fetch_organization_id_and_name, fetch_id_and_name
from utils.get_hierarchy import get_child_organization, get_organization_ids_by_scope_group, get_heirarchy
import traceback

ScopeGroupRouter = sgr = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "scope-group"
db_model = ScopeGroup

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

@sgr.get(endpoint['get'])
def get_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:  
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        if tenant == "provider":
            current_tenant = session.exec(select(Organization).where(Organization.id == current_user.organization)).first()
        else :
            current_tenant = session.exec(select(Organization).where(Organization.tenant_hashed == tenant)).first()
        
        # print("current tenant", get_child_organization(session, current_user.organization) )
        if not current_tenant:
            raise HTTPException(status_code=404, detail="Tenant organization not found")

        entries_list = session.exec(
            select(ScopeGroup)
            .join(ScopeGroupLink, ScopeGroup.id == ScopeGroupLink.scope_group)
            .where(ScopeGroup.tenant_id == current_tenant.id)
            .distinct()
        ).all()

        
        if not entries_list:
            raise HTTPException(status_code=404, detail="No scope groups found for your organization")
        
        scope_group_list = []
        for scope_group in entries_list:
            scope_group_list.append({
                "id": scope_group.id,
                "name": scope_group.name,
                "organizations": [org.name for org in scope_group.organizations],
            })

        return scope_group_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    
@sgr.get("/get-scope-group/{id}")
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
        entry = session.exec(select(db_model).where(db_model.id == id)).first()  
        if not entry:
            raise HTTPException(status_code=404, detail="Scope Group not found")
              
        return {
                "id": entry.id,
                "name": entry.name,
                "hidden": [org.id for org in entry.organizations],
            }
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")  
    
@sgr.get("/scope-group-form/")
async def form_scope_organization(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        heirarchy = get_heirarchy(session, current_user.organization, None, current_user, children_key="children")
            
        return {"data": {'id': "", 'name': "", "hidden": [heirarchy]} , "html_types": get_html_types("scope_group")}
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    
@sgr.post("/create-scope-group/")
async def add_organization_to_scope(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    valid: TemplateView
):
    try:
        if not check_permission(
            session, "Create", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        existing_scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.name == valid.name)).first()
        
        if existing_scope_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scope group already exists",
            )
        if tenant == "provider":
            current_tenant = session.exec(select(Organization).where(Organization.id == current_user.organization)).first()
        else :
            current_tenant = session.exec(select(Organization).where(Organization.tenant_hashed == tenant)).first()
        
        scope_group = ScopeGroup(
            name= valid.name,
            tenant_id = current_tenant.id
        )
        
        session.add(scope_group)
        session.commit()
        session.refresh(scope_group)
     
        #Add new entries
        to_add = set(valid.hidden)
        for org_id in to_add:
            scope_group_link_add = ScopeGroupLink(
                scope_group=scope_group.id,
                organization=org_id
                )
            session.add(scope_group_link_add)
            session.commit()
            session.refresh(scope_group_link_add)
           

        return {"Scope Group created successfully"}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    
@sgr.put("/update-scope-group/")
async def update_scope_group(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str,
    valid: UpdateTemplateView
):
    try:
        if not check_permission(
            session, "Update", role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )        
        scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == valid.id)).first()
        if not scope_group:
            raise HTTPException(status_code=404, detail="Role not found")
        
      
        if validate_name(valid.name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scope group name is not valid",
        )
        
        scope_group.name = valid.name
        session.add(scope_group)
        session.commit()
        session.refresh(scope_group)
        
        existing_orgs = [organization.id for organization in scope_group.organizations ]
        existing_org_ids = set(existing_orgs)
        new_org_ids_set = set(valid.hidden)
        print("existing", existing_org_ids)
        print("new", new_org_ids_set)
        # Add new entries
        to_add = new_org_ids_set - existing_org_ids
        for org_id in to_add:
            scope_group_link_add = ScopeGroupLink(scope_group= valid.id, organization=org_id)
            session.add(scope_group_link_add)
            session.commit()
            session.refresh(scope_group_link_add)


      # Remove obsolete entries
        to_remove = existing_org_ids - new_org_ids_set
        if to_remove:
            links_to_remove = session.exec(
                select(ScopeGroupLink)
                .where(ScopeGroupLink.scope_group == valid.id)
                .where(ScopeGroupLink.organization.in_(to_remove))
            ).all()

            for link in links_to_remove:
                session.delete(link)
                session.commit()

        return scope_group.id
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
     
@sgr.delete("/delete-scope-group/{id}")
async def delete_scope_group(
    session: SessionDep,
    id: int,
    current_user: UserDep,
):
    try:
        # Permission check
        if not check_permission(session, "Delete", "Administrative", current_user):
            raise HTTPException(status_code=403, detail="You do not have the required privilege")

        # Ensure scope group exists before proceeding
        scope_group = session.get(ScopeGroup, id)
        if not scope_group:
            raise HTTPException(status_code=404, detail="Scope group not found")

        # Delete links associated with the scope group
        scope_group_links = session.exec(select(ScopeGroupLink).where(ScopeGroupLink.scope_group == id)).all()
        for link in scope_group_links:
            session.delete(link)

        # Unassign users from the scope group
        assigned_users = session.exec(select(User).where(User.scope_group == id)).all()
        for user in assigned_users:
            user.scope_group = None
            session.add(user)  # mark for update

        # Delete the scope group
        session.delete(scope_group)
        session.commit()
        session.refresh(scope_group)

        return {"message": f"{endpoint_name} deleted successfully"}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
