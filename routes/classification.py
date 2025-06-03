from typing import Annotated, List, Dict, Any, Optional
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from utils.model_converter_util import get_html_types

from models.Account import Organization
from models.PointOfSale import PointOfSale
from utils.util_functions import validate_name
from models.Marketing import ClassificationGroup, CustomerDiscount
from utils.auth_util import get_current_user, check_permission
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_point_of_sale_id_and_name, fetch_organization_id_and_name
import traceback

classificationRouter = cr = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


@cr.get("/get-classification")
def get_classification(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

):
    try:
        if not check_permission(
            session, "Read",["Administrative", "Classification"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        classifications = session.exec(select(ClassificationGroup)).all()
        return classifications
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@cr.get("/get-classification/{classification_id}")
def get_classification(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,
):
    try:
        if not check_permission(
            session, "Read",["Administrative", "Classification"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        classification = session.exec(select(ClassificationGroup).where(ClassificationGroup.id == id))
        if not classification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="organization not found for the logged-in user",
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@cr.get("/classification-form")
async def get_form_fields_for_classification(
    session: SessionDep, current_user: UserDep
):
    try:
        if not check_permission(
            session, "Read",["Administrative", "Classification"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            ) 

        classification_data = {
            "id": "",
            "name": "",
            "description": "",
            "organization": fetch_organization_id_and_name(session, current_user),
            "point_of_sale": fetch_point_of_sale_id_and_name(session, current_user),
            "territory": fetch_territory_id_and_name(session, current_user),
            "route":"",
            "customer discount": ""
        }

        return {"data": classification_data, "html_types": get_html_types("classification")}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@cr.post("/create-classification")
async def create_classification(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

    name: str =Body(...),
    description: str =Body(...),
    organization: str =Body(...),
    territory: str =Body(...),
    route: str = Body(...),
    point_of_sale: str =Body(...),

 ):
    try:
        if not check_permission(
            session, "Create",["Administrative", "Category"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            ) 
        
        classification = ClassificationGroup(
            id= None,
            name = name,
            description = description,
            organization_id = organization,
            territory_id= territory,
            route_id = route,
            point_of_sale_id= point_of_sale
        )
        
        session.add(classification)
        session.commit()
        session.refresh(classification)
        
        return {"Classification created successfuly"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@cr.put("/update-classification/")
def update_classification(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

    name: str =Body(...),
    description: str =Body(...),
    organization: str =Body(...),
    territory: str =Body(...),
    route: str = Body(...),
    point_of_sale: str =Body(...),

 ):
    try:
        if not check_permission(
            session, "Update",["Administrative", "Category"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            ) 
        
        exisiting_classification = session.exec(select(ClassificationGroup).where(ClassificationGroup.id == id)).first()

        id= None,
        exisiting_classification.name = name,
        exisiting_classification.description = description,
        exisiting_classification.organization_id = organization,
        exisiting_classification.territory_id= territory,
        exisiting_classification.route_id = route,
        exisiting_classification.point_of_sale_id= point_of_sale

        
        session.add(exisiting_classification.classification)
        session.commit()
        session.refresh(exisiting_classification.classification)
        
        return {"Classification Updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@cr.delete("/delete-classification/{classification_id}")
def delete_classification(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

):
    try:
        if not check_permission(
            session, "Delete", "Classification", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        classification = session.get(ClassificationGroup, id)
        if not classification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Classification not found",
            )

        # Delete the classification
        session.delete(classification)
        session.commit()
        print()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@cr.get("/customer-discount-form")
async def get_form_fields_for_customer_discount(
    session: SessionDep, current_user: UserDep
):
    try:
        if not check_permission(
            session, "Read",["Administrative", "Discount"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            ) 

        # organization_rows = session.exec(
        #     select(Organization.id, Organization.organization_name)
        # ).all()

        # organization_dict = {row[0]: row[1] for row in organization_rows}

        # point_of_sale_rows = session.exec(
        #     select(PointOfSale.id, PointOfSale.company_name)
        # ).all()

        # point_of_sale_dict = {row[0]: row[1] for row in point_of_sale_rows}

        customer_discount = CustomerDiscount(
            id="",
            start_date="",
            end_date="",
            discount="",
            classification_group="",
            slip=""
        )
        return {"data": customer_discount, "html_types": get_html_types("discount")}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))