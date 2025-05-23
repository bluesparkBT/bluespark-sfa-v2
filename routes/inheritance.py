from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Annotated, List, Dict, Any, Optional
from utils.auth_util import get_current_user, check_permission
from utils.form_db_fetch import add_category_link, add_product_link
from db import SECRET_KEY, get_session
from models.Account import User, AccessPolicy, Organization, OrganizationType, ScopeGroup, Scope, Role, ScopeGroupLink
from models.Product import Product, Category
from utils.model_converter_util import get_html_types

from utils.form_db_fetch import get_organization_ids_by_scope_group
import traceback

from sqlmodel import select, Session
from models import InheritanceGroup

InheritanceRouter =In= APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

@In.get("/get-inheritances")
async def get_inheritance_groups(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str,
):
    try: 
        if not check_permission(
            session, "Read", ["Inheritance", "Administrative"], current_user):
            raise HTTPException(
                status_code=403, detail="You do not have the required privilege")   

        # Fetch all inheritance groups from the table
        inheritance_groups = session.exec(select(InheritanceGroup)).all()

        if not inheritance_groups:
            raise HTTPException(status_code=404, detail="No inheritance groups found")

        return inheritance_groups

    except Exception as e:
        traceback.format_exc()
        raise HTTPException(status_code=400, detail=str(e))

@In.get("/get-inheritance/{inheritance_id}")

@In.get("/inheritance-form/")
def het_inheritance_form(
     tenant: str,
    session: SessionDep,
    current_user: UserDep,   
):
    try:
        # Check permission
        if not check_permission(
            session, "Create",["Administrative", "Inheritance"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )   

        form_structure = {
            "id": "",
            "name": "",
            # "parent_category": fetch_category_id_and_name(session, current_user),
      } 

        return {"data": form_structure, "html_types": get_html_types("Inheritance")}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))    


async def get_inheritance_group(
    session: SessionDep,
    current_user: UserDep,
    tenant : str,
    inheritance_id: int, 

):
    try:
        if not check_permission(
            session, "Read",[ "Inheritance", "Administrative"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )   
        db_inheritance = session.exec(
            select(InheritanceGroup).where(InheritanceGroup.id == inheritance_id)
        ).first()
        print(InheritanceGroup.id)

        if not db_inheritance:
            raise HTTPException(status_code=404, detail="Inheritance group not found")

        return db_inheritance
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 

@In.post("/create-inheritance")
async def create_inheritance_group(
    session: SessionDep,
    current_user: UserDep,
    tenant : str,
    name: str = Body(...), 
    products: int = Body(...),
    category: int = Body(...)


):
    """
    """
    try:
        if not check_permission(
            session, "Create", ["Inheritance", "Administrative"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        new_group = InheritanceGroup(
            name=name

            )
        session.add(new_group)
        session.commit()
        
        return {"message": "Inheritance group created"}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@In.post("/add-inheritance/")
async def add_inheritance_group(             
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    inheritance_id: int = Body(...),
    category_id: int | str = Body(...),
    product_id: int | str = Body(...),
):
    inheritance_group = session.exec(
            select(Organization.inheritance_group).where(Organization.id == current_user.organization_id)
        ).first()
    if not inheritance_group:
        raise HTTPException(status_code=404, detail="Inheritance group not found")
    
    if category_id:
        check_category = session.exec(
                select(Category).where(Category.id == category_id)
            ).first()
        if check_category.organization_id != None:
            category_link_status = add_category_link(session,inheritance_id, category_id)
    else:
        category_link_status = {"message": "catagory not defined"}
    if product_id:

        check_product = session.exec(
                select(Product).where(Product.id == product_id)
            ).first()
        if check_product.organization_id != None:
            product_link_status = add_product_link(session, inheritance_id, product_id)
    else:
        product_link_status =  {"message": "product not defined"}

    
  
    return {"message": {"Category": category_link_status, "Product": product_link_status}}

@In.put("/update-inheritance/{inheritance_id}")
async def update_inheritance_group(
    session: SessionDep,
    current_user: UserDep,
    inheritance_id: int, 
    new_inheritance_name: str = Body(...)
):
    try:
        if not check_permission(
                session, "Read",[ "Inheritance", "Administrative"], current_user
                ):
                raise HTTPException(
                    status_code=403, detail="You Do not have the required privilege"
                )   
        db_inheritance = session.exec(
                select(InheritanceGroup).where(InheritanceGroup.id == inheritance_id)
            ).first()  
        if not db_inheritance:
            raise HTTPException(status_code=404, detail="Inheritance group not found")
        db_inheritance.name = new_inheritance_name
        session.add(db_inheritance)
        session.commit()
        session.refresh(db_inheritance) 

        return {
                    "message": "Product updated successfully",
            }   
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
@In.delete("/delete-inheritance/{inheritance_id}")
async def delete_inheritance_group(
    session: SessionDep,
    current_user: UserDep,
    inheritance_id: int, 
):
    if not check_permission(
            session, "Read",[ "Inheritance", "Administrative"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )   
    db_inheritance = session.exec(
            select(InheritanceGroup).where(InheritanceGroup.id == inheritance_id)
        ).first()
    if not db_inheritance:
        raise HTTPException(status_code=404, detail="Inheritance group not found")

    session.delete(db_inheritance)
    session.commit()
    return {"message": "Inheritance group deleted"}