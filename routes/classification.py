
from typing import Annotated, List, Dict, Any, Optional, Union
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from utils.model_converter_util import get_html_types
from models.Marketing import ClassificationGroup
from utils.util_functions import validate_name
from models.viewModel.ClassificationView import ClassificationView as TemplateView #Update this
from models.viewModel.ClassificationView import updateClassificationView as TemplateViews
from utils.auth_util import get_current_user, check_permission, check_permission_and_scope
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import (fetch_point_of_sale_ids, 
                                 fetch_organization_id_and_name, 
                                 fetch_discount_id_and_name,
                                 fetch_territory_id_and_name,
                                 fetch_route_id_and_name)
import traceback

#Update router name
ClassificationRouter= c = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "classification" #Update this
db_model = ClassificationGroup #Update this

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
    "get": ["Administrative","Classification"],
    "get_form": ["Administrative","Classification"],
    "create": ["Administrative","Classification"],
    "update": ["Administrative","Classification"],
    "delete": ["Administrative","Classification"],
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
        if not entries_list:
             raise HTTPException(status_code=404, detail=" classification not found")

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
    # valid: TemplateView,
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
        classification= {
        "id": entry.id,
        "name": entry.name,
        "description": entry.description,
        "organization": entry.organization,
        "point_of_sale": entry.point_of_sale_id,
        "territory":entry.territory_id,
        "route":entry.route_id,
        "customer_discount": entry.customer_discounts,
        }
        #Business Logic
        return classification
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")




@c.get("/classification-form")
async def get_form_fields_for_classification(
    session: SessionDep, current_user: UserDep
):
    try:
        if not check_permission(
            session, "Create",role_modules['get_form'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )   

        classification_data = {
            "id": "",
            "name": "",
            "organization": fetch_organization_id_and_name(session, current_user),
            "point_of_sale": fetch_point_of_sale_ids(session, current_user),
            "route":fetch_route_id_and_name(session, current_user),
            "territory": fetch_territory_id_and_name(session, current_user),
            "description": "",
            "customer_discount": fetch_discount_id_and_name(session, current_user)
        }

        return {"data": classification_data, "html_types": get_html_types("classification")}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))






#Create entry template 
@c.post(endpoint['create'])
def create_template(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    valid: TemplateView,
):
    try:
        # Create a new category entry from validated input
        if not check_permission(
            session, "Create", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        new_entry = db_model.model_validate(valid)  
        print(valid.customer_discounts)      
        
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
    valid: TemplateViews,
):
    try:
        # Check permission
        if not check_permission(
            session, "Update", role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        selected_entry = session.exec(
            select(db_model).where(db_model.organization.in_(organization_ids), db_model.id == valid.id)
        ).first()

        if not selected_entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")
        
        # if valid.organization == organization_ids:
        selected_entry.organization = valid.organization
        selected_entry.name = valid.name
        selected_entry.point_of_sale_id = valid.point_of_sale
        selected_entry.territory_id = valid.territory
        selected_entry.route_id = valid.route
        selected_entry.customer_discounts = valid.customer_discount
        selected_entry.description = valid.description



        # else:
        #     {"message": "invalid input select your own organization id"}    
 
        # Commit the changes and refresh the object
        session.add(selected_entry)
        session.commit()
        session.refresh(selected_entry)

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

    
        # Delete category after validation
        session.delete(selected_entry)
        session.commit()

        return {"message": f"{endpoint_name} deleted successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
