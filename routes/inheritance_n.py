from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Annotated, List, Dict, Any, Optional
from utils.auth_util import get_current_user, check_permission
from utils.form_db_fetch import add_category_link, add_product_link
from db import SECRET_KEY, get_session
from models.Account import User, AccessPolicy, Organization, OrganizationType, ScopeGroup, Scope, Role, ScopeGroupLink
from models.Product_Category import Product, Category,ProductLink, CategoryLink,InheritanceGroup
from utils.model_converter_util import get_html_types
from utils.form_db_fetch import fetch_category_id_and_name, fetch_product_id_and_name, fetch_role_id_and_name, fetch_classification_id_and_name, fetch_point_of_sale_id_and_name
import traceback
from sqlmodel import delete

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


@In.get("/inheritance-form/")
def inheritance_form(
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
            "category": fetch_category_id_and_name(session, current_user) ,
            "product": fetch_product_id_and_name(session, current_user),
            "role": fetch_role_id_and_name(session, current_user),
            "classification": fetch_classification_id_and_name(session, current_user),  
            "point_of_sale": fetch_point_of_sale_id_and_name(session, current_user),
      } 

        return {"data": form_structure, "html_types": get_html_types("inheritance")}

    except Exception as e:
        traceback.print_exc()
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

        return {
            "id": db_inheritance.id,
            "inheritance_name": db_inheritance.name
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e)) 

@In.post("/add-inheritance/")
async def add_inheritance_group(             
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    name: str = Body(...),
    category: int | str = Body(None),  # Default to None if not provided
    product: int | str = Body(None),   # Default to None if not provided
):
    try:
        if not check_permission(
            session, "Create", "Inheritance", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        # Initialize status variables
        category_link_status = {"message": "Category not processed"}
        product_link_status = {"message": "Product not processed"}

        # Check if inheritance group already exists
        check_inheritance_exist = session.exec(
            select(InheritanceGroup).where(InheritanceGroup.name == name)
        ).first()

        if check_inheritance_exist:
            raise HTTPException(status_code=400, detail="Inheritance already exists")
        
        # Create a new inheritance group
        new_group = InheritanceGroup(name=name)
        session.add(new_group)
        session.commit()

        # Category processing (only if provided)
        if category:
            check_category = session.exec(
                select(Category).where(Category.id == category)
            ).first()

            if check_category:
                existing_link = session.exec(
                    select(CategoryLink).where(
                        CategoryLink.inheritance_group_id == new_group.id,
                        CategoryLink.category_id == category
                    )
                ).first()

                if existing_link:
                    category_link_status = {"message": "Category already linked to inheritance group"}
                else:
                    new_category_link = CategoryLink(
                        inheritance_group_id=new_group.id,
                        category_id=category
                    )
                    session.add(new_category_link)
                    session.commit()
                    session.refresh(new_category_link)
                    category_link_status = {"message": "Category linked successfully"}
            else:
                category_link_status = {"message": "Category not defined"}

        # Product processing (only if provided)
        if product:
            check_product = session.exec(
                select(Product).where(Product.id == product)
            ).first()

            if check_product:
                existing_product_link = session.exec(
                    select(ProductLink).where(
                        ProductLink.inheritance_group_id == new_group.id,
                        ProductLink.product_id == product
                    )
                ).first()

                if existing_product_link:
                    product_link_status = {"message": "Product already linked to inheritance group"}
                else:
                    new_product_link = ProductLink(
                        inheritance_group_id=new_group.id,
                        product_id=product
                    )
                    session.add(new_product_link)
                    session.commit()
                    session.refresh(new_product_link)
                    product_link_status = {"message": "Product linked successfully"}
            else:
                product_link_status = {"message": "Product not defined"}

        return {"message": {"Category": category_link_status, "Product": product_link_status}}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@In.put("/update-inheritance/")
async def update_inheritance_group(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    inheritance_id: int = Body(...), 
    new_inheritance_name: str = Body(...)
):
    try:
        if not check_permission(
            session, "Update",[ "Inheritance", "Administrative"], current_user
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

        return {"message": "Product updated successfully" }   
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
    

@In.delete("/delete-inheritance/{inheritance_id}")
async def delete_inheritance_group(
    session: SessionDep,
    current_user: UserDep,
    inheritance_id: int, 
):
    if not check_permission(
        session, "Read", ["Inheritance", "Administrative"], current_user
    ):
        raise HTTPException(
            status_code=403, detail="You do not have the required privilege"
        )   

    db_inheritance = session.exec(
        select(InheritanceGroup).where(InheritanceGroup.id == inheritance_id)
    ).first()

    if not db_inheritance:
        raise HTTPException(status_code=404, detail="Inheritance group not found")

    # Delete associated category links
    session.exec(
        delete(CategoryLink).where(CategoryLink.inheritance_group_id == inheritance_id)
    )

    # Delete associated product links
    session.exec(
        delete(ProductLink).where(ProductLink.inheritance_group_id == inheritance_id)
    )

    # Delete the inheritance group itself
    session.delete(db_inheritance)
    session.commit()

  