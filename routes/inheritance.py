from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, List, Dict, Any, Optional
from utils.auth_util import get_current_user, check_permission
from utils.form_db_fetch import (
    add_category_link,
    add_product_link,)
from db import SECRET_KEY, get_session
from models.Account import User, AccessPolicy, Organization, OrganizationType, ScopeGroup, Scope, Role, ScopeGroupLink
from models.Product import Product, Category

from sqlmodel import select, Session
from models import InheritanceGroup

InheritanceRouter =In= APIRouter()
# GET: Retrieve an inheritance group by ID

SessionDep = Annotated[Session, Depends(get_session)]

# POST: Create a new inheritance group
@In.post("/create-inheritance", response_model=Dict[str, Any])
def create_inheritance_group(
                             name: str, 
                             session: SessionDep,
                             current_user: User = Depends(get_current_user),):

    new_group = InheritanceGroup(name=name)
    session.add(new_group)
    session.commit()
    session.refresh(new_group)
    return {"message": "Inheritance group created", "group": new_group}

@In.get("/get-inheritance/{inheritance_id}", response_model=InheritanceGroup)
def get_inheritance_group(
                             inheritance_id: int, 
                             name: str, 
                             session: SessionDep,
                             category: Category ,
                             current_user: User = Depends(get_current_user)
):
    inheritance_group = session.exec(
            select(Organization.inheritance_group).where(Organization.id == current_user.organization_id)
        ).first()
    if not inheritance_group:
        raise HTTPException(status_code=404, detail="Inheritance group not found")

    return inheritance_group




#  PUT: Update an existing inheritance group

@In.post("/add-inheritance/")
def add_inheritance_group(
                             
                             name: str,
                             new_inheritance_id: int,
                             session: SessionDep,
                             new_category_id: int,
                             new_product_id: int,
                             current_user: User = Depends(get_current_user)):
    inheritance_group = session.exec(
            select(Organization.inheritance_group).where(Organization.id == current_user.organization_id)
        ).first()
    if not inheritance_group:
        raise HTTPException(status_code=404, detail="Inheritance group not found")
    check_category = session.exec(
            select(Category).where(Category.id == new_category_id)
        ).first()
    check_product = session.exec(
            select(Product).where(Product.id == new_product_id)
        ).first()
    
    if check_category.organization_id != None:

        add_category_link(session,new_inheritance_id, new_category_id)
 
    if check_product.organization_id != None:
        add_product_link(session, new_inheritance_id, new_product_id)


    # Check if the inheritance group already existsi
    
  
    return {"message": "Inheritance group updated"}

# DELETE: Remove an inheritance group
@In.delete("/delete-inheritance/{inheritance_id}")
def delete_inheritance_group(
                             inheritance_id: int, 
                             name: str, 
                             session: SessionDep,
                             category: Category ,
                             current_user: User = Depends(get_current_user)
):
    inheritance_group = session.exec(
            select(Organization.inheritance_group).where(Organization.id == current_user.organization_id)
        ).first()

    if not inheritance_group:
        raise HTTPException(status_code=404, detail="Inheritance group not found")

    session.delete(inheritance_group)
    session.commit()
    return {"message": "Inheritance group deleted"}