from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Annotated, List, Dict, Any, Optional
from utils.auth_util import get_current_user, check_permission
from utils.form_db_fetch import add_category_link, add_product_link
from db import SECRET_KEY, get_session
from models.Account import User, AccessPolicy, Organization, OrganizationType, ScopeGroup, Scope, Role, ScopeGroupLink
from models.Product import Product, Category
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


#@In.post("/add-inheritance/")
# async def add_inheritance_group(             
#     session: SessionDep,
#     current_user: UserDep,
#     new_inheritance_id: int,
#     name: str,
#     new_category_id: int,
#     new_product_id: int,
# ):
#     inheritance_group = session.exec(
#             select(Organization.inheritance_group).where(Organization.id == current_user.organization_id)
#         ).first()
#     if not inheritance_group:
#         raise HTTPException(status_code=404, detail="Inheritance group not found")
#     check_category = session.exec(
#             select(Category).where(Category.id == new_category_id)
#         ).first()
#     check_product = session.exec(
#             select(Product).where(Product.id == new_product_id)
#         ).first()
    
#     if check_category.organization_id != None:

#         add_category_link(session,new_inheritance_id, new_category_id)
 
#     if check_product.organization_id != None:
#         add_product_link(session, new_inheritance_id, new_product_id)


    # Check if the inheritance group already existsi
    
  
    #return {"message": "Inheritance group updated"}

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