from typing import Annotated, List, Dict, Any, Optional, Union
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from utils.model_converter_util import get_html_types
from models.Account import User, ScopeGroup,ScopeGroupLink, Organization, Role
from models.RoutesAndVisits import Route
from utils.util_functions import validate_name
from models.viewModel.Search import SearchPagination as pagination
from models.viewModel.TerritoryView import RouteView as TemplateView ,  updateRouteView as updaterouteview
from utils.auth_util import get_current_user, check_permission, check_permission_and_scope
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_territory_id_and_name, fetch_organization_id_and_name, fetch_id_and_name
from sqlmodel import SQLModel, Field, Session, select
from datetime import date
import traceback
# Update router name
RouteRouter = c = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "route"  # Update this
db_model = Route  # Update this

endpoint = {
    "get": f"/get-{endpoint_name}",
    "get_by_id": f"/get-{endpoint_name}/{{id}}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",
    "update": f"/update-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}

# Update role_modules
role_modules = {
    "get": ["Administrative"],
    "get_form": ["Administrative"],
    "create": ["Administrative"],
    "update": ["Administrative"],
    "delete": ["Administrative"],
}

# CRUD Operations
def select_heroes():
    with Session(engine) as session:
        statement = select(Hero).offset(6).limit(3)
        results = session.exec(statement)
        heroes = results.all()
        print(heroes)

@c.get(endpoint['get'])
def get_routes(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    page: int,
    pageSize: int,
    searchString: Optional[str]

):
    try:
        orgs_in_scope = check_permission_and_scope(session, "Read", role_modules['get'], current_user)
        pagestart= page * pageSize
        pagesize = pageSize
        
        entry = select(db_model).where(db_model.organization.in_(orgs_in_scope["organization_ids"])).offset(pagestart).limit(pagesize)
        
        results = session.exec(entry)
        entries_list = results.all()
        return {
            "succeed": True,
            "error": f"{endpoint_name} found",
            "data":  { 
                "total": 10,
                "items":  entries_list,
                "paginationInfo":  { 
                    "page": page, 
                    "pageSize": pageSize,
                    "totalItems": 100, 
                    "searchString": searchString,
                    # You can calculate the following from above 
                    # index or skip => pageSize * (page - 1) 
                    # totalPages = (int)Math.Ceiling(1.0 * totalItems / pageSize);
                    # hasPrevious => page > 1 
                    # hasNext => page < totalPages
                }
            }
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        return {
                "succeed": False,
                "error": "Something went wrong",
                "data":  None
                }


@c.get(endpoint['get_by_id'])
def get_route_by_id(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int
):
    try:
        if not check_permission(session, "Read", role_modules['get'], current_user):
            raise HTTPException(status_code=403, detail="You do not have the required privilege")

        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        entry = session.exec(
            select(db_model).where(db_model.organization.in_(organization_ids), db_model.id == id)
        ).first()

        if not entry:
            return {
            "succeed": False,
            "error": f"{endpoint_name} not found",
            "data":  None
            }
        
        route= {
            "id": entry.id,
            "name": entry.name,
            "territory": entry.territory,
            "description": entry.description,
            "organization": entry.organization, 
         }
        
        return {
        "succeed": True,
        "error": f"{endpoint_name} found",
        "data": route
    }
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        return {
            "succeed": False,
            "error": f"something went wrong",
            "data":  None
            }

@c.get(endpoint["get_form"])
def get_form_fields_for_route(
    session: SessionDep, current_user: UserDep
):
    try:
        # ter= fetch_territory_id_and_name(session, current_user)
        # print(ter)
        if not check_permission(
            session, "Create",role_modules['get_form'], current_user
            ):
  
            return {
                    "succeed": False,
                    "error": "You Do not have the required privilege",
                    "data":  None
                    }
        route_data = {
            "id": "",
            "name": "",
            "territory": fetch_territory_id_and_name(session, current_user),
            "description": "",
            "organization": fetch_organization_id_and_name(session, current_user)
            }

        return {"data": route_data, "html_types": get_html_types("route")}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@c.post(endpoint['create'])
def create_route(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    valid: TemplateView
):
    try:
        new_entry = db_model.model_validate(valid)

        session.add(new_entry)
        session.commit()
        session.refresh(new_entry)

        return {
            "succeed": True,
            "error": f"{endpoint_name} creted successfully",
            "data":  new_entry
            }

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        return {
                "succeed": False,
                "error": "Something went wrong",
                "data":  None
                }

@c.put(endpoint['update'])
def update_route(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    valid: updaterouteview,
):
    try:
        if not check_permission(session, "Update", role_modules['update'], current_user):
            return {
                    "succeed": False,
                    "error": "You Do not have the required privilege",
                    "data":  None
                    }        
   
        entry = session.get(db_model, valid.id)

        if not entry:
                  return {
            "succeed": False,
            "error": f"{endpoint_name} not found",
            "data":  None
            }

        # Update fields
        entry.name = valid.name
        entry.territory = valid.territory
        entry.description = valid.description
        entry.organization = valid.organization

        session.add(entry)
        session.commit()
        session.refresh(entry)

        return {
            "succeed": True,
            "error": f"{endpoint_name} updated sucessfuly",
            "data":  entry
            }

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        return {
            "succeed": False,
            "error": f"something went wrong",
            "data":  None
            }


@c.delete(endpoint['delete'] + "/{id}")
def delete_route(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    id: int
):
    try:
        if not check_permission(session, "Delete", role_modules['delete'], current_user):
            return {
                    "succeed": False,
                    "error": "You Do not have the required privilege",
                    "data":  None
                    }  
        entry = session.get(db_model, id)

        if not entry:
            return {
                    "succeed": False,
                    "error": f"{endpoint_name} not found",
                    "data":  None
                    }
        session.delete(entry)
        session.commit()

        return {
            "succeed": False,
            "error": f"{endpoint_name} deleted sucessfully",
            "data":  None
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        return {
            "succeed": False,
            "error": f"something went wrong",
            "data":  None
            }