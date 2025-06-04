from typing import Annotated, List, Dict, Any, Optional, Union
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from utils.model_converter_util import get_html_types
from models.Account import User, ScopeGroup,ScopeGroupLink, Organization, Role
from models.Marketing import CustomerDiscount
from utils.util_functions import validate_name
from models.viewModel.ClassificationView import CustomerDiscountView as TemplateView ,  UpdateCustomerDiscountView as TemplateViews 
from utils.auth_util import get_current_user, check_permission, check_permission_and_scope
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_category_id_and_name, fetch_organization_id_and_name, fetch_id_and_name
from sqlmodel import SQLModel, Field, Session, select
from datetime import date
import traceback

# Update router name
CustomerDiscountRouter = c = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "customer-discount"  # Update this
db_model = CustomerDiscount  # Update this

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
    "get": ["Administrative", "Classification"],
    "get_form": ["Administrative", "Classification"],
    "create": ["Administrative", "Classification"],
    "update": ["Administrative", "Classification"],
    "delete": ["Administrative", "Classification"],
}

# CRUD Operations

@c.get(endpoint['get'])
def get_customer_discounts(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        orgs_in_scope = check_permission_and_scope(session, "Read", role_modules['get'], current_user)

        entries_list = session.exec(
            select(db_model)
        ).all()

        return entries_list

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")


@c.get(endpoint['get_by_id'])
def get_customer_discount_by_id(
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
            select(db_model).where( db_model.id == id)
        ).first()

        if not entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

        return entry

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")


@c.post(endpoint['create'])
def create_customer_discount(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    valid: TemplateView
):
    try:
        # Ensure required fields are present
        if valid.discount is None:
            raise HTTPException(status_code=400, detail="Discount field is required")

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
def update_customer_discount(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    id: int,
    valid: TemplateViews
):
    try:
        if not check_permission(session, "Update", role_modules['update'], current_user):
            raise HTTPException(status_code=403, detail="You do not have the required privilege")

        entry = session.get(db_model, id)

        if not entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

        # Update fields
        entry.start_date = valid.start_date
        entry.end_date = valid.end_date
        entry.discount = valid.discount

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
def delete_customer_discount(
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