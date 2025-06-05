import traceback
from fastapi import Depends, HTTPException, Body, APIRouter
from typing import Annotated, Optional
from fastapi.routing import APIRouter
from sqlmodel import and_, select, Session
from db import get_session
from models.PointOfSale import PointOfSale
from models.Utils import ErrorLog
from utils.address_util import check_address
from utils.auth_util import get_current_user
from models.viewModel.pointOfSaleView import PointOfSaleView as TemplateView , UpdatePointOfSaleView as TemplateViews

from utils.model_converter_util import get_html_types
from utils.auth_util import check_permission, check_permission_and_scope
from utils.form_db_fetch import( get_organization_ids_by_scope_group,
                                fetch_wakl_in_customer_id_and_name,
                                fetch_outlet_id_and_name
                                ) 

# Update router name
PointOfSaleRouter = c = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "point-of-sale"  # Update this
db_model = PointOfSale  # Update this

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

@c.get(endpoint['get'])
def get_point_of_sales(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        orgs_in_scope = check_permission_and_scope(session, "Read", role_modules['get'], current_user)

        entries_list = session.exec(
            select(db_model).where(db_model.organization.in_(orgs_in_scope["organization_ids"]))
        ).all()

        return entries_list

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")


@c.get(endpoint['get_by_id'])
def get_point_of_sale_by_id(
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
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

        return entry

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")



@c.get (endpoint['get_form'])
def point_of_sale_form(
    tenant: str,
    session: SessionDep,
    current_user: UserDep,   
):
    try:
        if not check_permission(
            session, "Create",role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        form_structure = {
            "id": "",
            "status": "",
            "organization": "",
            "outlet": fetch_outlet_id_and_name(session, current_user),
            "walk_in_customer": fetch_wakl_in_customer_id_and_name(session, current_user),
   
      } 

        return {"data": form_structure, "html_types": get_html_types("inheritance")}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

@c.post(endpoint['create'])
def create_point_of_sale(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    valid: TemplateView
):
    try:
        if not check_permission(session, "Create", role_modules['create'], current_user):
            raise HTTPException(status_code=403, detail="You do not have the required privilege")

        new_entry = db_model.model_validate(valid)

        session.add(new_entry)
        session.commit()
        session.refresh(new_entry)

        return new_entry

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")


@c.put(endpoint['update'])
def update_point_of_sale(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    id: int,
    valid: TemplateViews
):
    try:
        if not check_permission(session, "Update", role_modules['update'], current_user):
            raise HTTPException(status_code=403, detail="You do not have the required privilege")

        entry = session.get(db_model, valid.id)

        if not entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

        # Update fields
        entry.status = valid.status
        entry.registered_on = valid.registered_on
        entry.organization = valid.organization
        entry.outlet_id = valid.outlet_id
        entry.walk_in_customer_id = valid.walk_in_customer_id

        session.add(entry)
        session.commit()
        session.refresh(entry)

        return entry

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")


@c.delete(endpoint['delete'])
def delete_point_of_sale(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    id: int
):
    try:
        if not check_permission(session, "Delete", role_modules['delete'], current_user):
            raise HTTPException(status_code=403, detail="You do not have the required privilege")

        entry = session.get(db_model, id)

        if not entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

        session.delete(entry)
        session.commit()

        return {"detail": f"{endpoint_name} deleted successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")