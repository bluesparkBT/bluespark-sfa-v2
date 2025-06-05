from sqlmodel import select, Session, delete
from fastapi import APIRouter, Depends, HTTPException, Body, Path
from typing import Annotated, List, Dict, Any, Optional
from utils.auth_util import get_current_user, check_permission
from utils.form_db_fetch import add_category_link, add_product_link
from db import SECRET_KEY, get_session
from models.Account import User, AccessPolicy, Organization, OrganizationType, ScopeGroup, Scope, Role, ScopeGroupLink
from models.Product_Category import Product, Category,ProductLink, CategoryLink,InheritanceGroup
from models.viewModel.InheritanceView import AddInheritanceView as AddTemplateView ,UpdateInheritanceView as TemplateView
from utils.get_hierarchy import get_organization_ids_by_scope_group

from utils.model_converter_util import get_html_types
from utils.form_db_fetch import fetch_category_id_and_name, fetch_product_id_and_name, fetch_role_id_and_name, fetch_classification_id_and_name, fetch_point_of_sale_ids
import traceback
from models import InheritanceGroup

endpoint_name = "inheritance"
db_model = InheritanceGroup

endpoint = {
    "get": f"/get-{endpoint_name}s",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",
    "add": f"/add-{endpoint_name}",

    "update": f"/update-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}
role_modules = {   
    "get": ["Administrative", "Inheritance"],
    "get_form": ["Administrative", "Inheritance"],
    "create": ["Administrative", "Inheritance"],
    "update": ["Administrative", "Inheritance"],
    "delete": ["Administrative", "Inheritance"],
}


InheritanceRouter =In= APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

@In.get(endpoint['get'])
async def get_inheritance_groups(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str,
):
    try: 
        if not check_permission(
            session, "Read",role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        # Fetch all inheritance groups from the table
        # inherited_group_id = session.exec(
        #     select(Organization.inheritance_group).where(Organization.id == current_user.organization)
        # ).first()
                
        # entry = session.exec(
        #     select(db_model).where(db_model.id == inherited_group_id)
        #     ).all()

        entry = session.exec(select(InheritanceGroup)).all()
        

        if not entry:
            raise HTTPException(status_code=404, 
                detail={"message": f"{endpoint_name} Group not found"})
        return entry

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

#Create entry 
@In.get(endpoint['get_form'])
def inheritance_form(
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
            "name": "",
            "category": fetch_category_id_and_name(session, current_user) ,
            "product": fetch_product_id_and_name(session, current_user),
            # "role": fetch_role_id_and_name(session, current_user),
            # "classification": fetch_classification_id_and_name(session, current_user),  
            # "point_of_sale": fetch_point_of_sale_id_and_name(session, current_user),
      
      } 

        return {"data": form_structure, "html_types": get_html_types("inheritance")}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

  
@In.get(endpoint['get_by_id'] + "/{id}")
async def get_inheritance_group(
    session: SessionDep,
    current_user: UserDep,
    tenant : str,
    id: int, 

):
    try:
        if not check_permission(
            session, "Read",role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )  

        # organization_ids = get_organization_ids_by_scope_group(session, current_user)
 
        # entry = session.exec(
        #     select(db_model).where(db_model.organization.in_(organization_ids), db_model.id == id)
        # ).first()
        # print(db_model.id)

        entry = session.exec(
            select(InheritanceGroup).where(InheritanceGroup.id == id)

        ).first()        

        if not entry:
            return {"message": f"{endpoint_name} not found"}

        return {
            "id": entry.id,
            "inheritance_name": entry.name
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

#Create entry 
# @In.post("/add-inheritance/")
# async def add_inheritance_group(             
#     session: SessionDep,
#     current_user: UserDep,
#     tenant: str,
#     inheritance_name: str = Body(...),
#     category: int | str = Body(...),
#     product: int | str = Body(...),
# ):
#     # Initialize status variables
#     category_link_status = {"message": "Category processing failed"}
#     product_link_status = {"message": "Product processing failed"}


#     check_inheritance_exist = session.exec(
#         select(InheritanceGroup).where(InheritanceGroup.name == inheritance_name)
#     ).first()
#     if check_inheritance_exist:
#         raise HTTPException (status_code=400, 
#                             detail= 'inheritance alredy exist')
    
            
#     new_group = InheritanceGroup(
#             name=inheritance_name)
    
#     session.add(new_group)
#     session.commit()
#     # Category processing
#     check_category = session.exec(
#         select(Category).where(Category.id == category)
#     ).first()
    
#     if check_category:
#         existing_link = session.exec(
#             select(CategoryLink).where(
#                 CategoryLink.inheritance_group_id == new_group.id,
#                 CategoryLink.category_id == category
#             )
#         ).first()
        
#         if existing_link:
#             category_link_status = {"message": "Category already linked to inheritance group"}
#         else:
#             new_category_link = CategoryLink(
#                 inheritance_group_id= new_group.id,
#                 category_id=category
#             )
#             session.add(new_category_link)
#             session.commit()
#             session.refresh(new_category_link)
#             category_link_status = {"message": "Category linked successfully"}
#     else:
#         category_link_status = {"message": "Category not defined"}

#     # Product processing
#     check_product = session.exec(
#         select(Product).where(Product.id == product)
#     ).first()
    
#     if check_product:
#         existing_product_link = session.exec(
#             select(ProductLink).where(
#                 ProductLink.inheritance_group_id == new_group.id,
#                 ProductLink.product_id == product
#             )
#         ).first()

#         if existing_product_link:
#             product_link_status = {"message": "Product already linked to inheritance group"}
#         else:
#             new_product_link = ProductLink(
#                 inheritance_group_id=new_group.id,
#                 product_id=product
#             )
#             session.add(new_product_link)
#             session.commit()
#             session.refresh(new_product_link)
#             product_link_status = {"message": "Product linked successfully"}
#     else:
#         product_link_status = {"message": "Product not defined"}

#     return {"message": {"Category": category_link_status, "Product": product_link_status}}

@In.post(endpoint['add'])
async def add_inheritance_group(             
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    valid: AddTemplateView  # Default to None if not provided
):
    try:
        if not check_permission(
            session, "Create", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        category_link_status = {"message": "Category not processed"}
        product_link_status = {"message": "Product not processed"}

        # Check if inheritance group already exists
        # organization_ids = get_organization_ids_by_scope_group(session, current_user)
 
        # check_inheritance_exist = session.exec(
        #     select(db_model).where(db_model.organization.in_(organization_ids), db_model.name == valid.name)
        # ).first()
        check_inheritance_exist = session.exec(
            select(db_model).where(db_model.name == valid.name)
        ).first()

        print(db_model.id)
        if check_inheritance_exist:
            raise HTTPException(status_code=400, detail={"message": f"{endpoint_name} already exist"})
        
        # Create a new inheritance group
        new_group = db_model(name=valid.name)
        session.add(new_group)
        session.commit()

        # Category processing (only if provided)
        if valid.category:
            #to select category only with in ur org
               # check_category = session.exec(
            #      select(Category).where(Category.organization.in_(organization_ids))
            # ).first()
            check_category = session.exec(
                select(Category).where(Category.id == valid.category)
            ).first()

            if check_category:
                existing_link = session.exec(
                    select(CategoryLink).where(
                        CategoryLink.inheritance_group_id == new_group.id,
                        CategoryLink.category_id == valid.category
                    )
                ).first()

                if existing_link:
                    category_link_status = {"message": "Category already linked to inheritance group"}
                else:
                    new_category_link = CategoryLink(
                        inheritance_group_id=new_group.id,
                        category_id=valid.category
                    )
                    session.add(new_category_link)
                    session.commit()
                    session.refresh(new_category_link)
                    category_link_status = {"message": "Category linked successfully"}
            else:
                category_link_status = {"message": "Category not defined"}

        # Product processing (only if provided)
        if valid.product:
            check_product = session.exec(
                select(Product).where(Product.id == valid.product)
            ).first()

            if check_product:
                existing_product_link = session.exec(
                    select(ProductLink).where(
                        ProductLink.inheritance_group_id == new_group.id,
                        ProductLink.product_id == valid.product
                    )
                ).first()

                if existing_product_link:
                    product_link_status = {"message": "Product already linked to inheritance group"}
                else:
                    new_product_link = ProductLink(
                        inheritance_group_id=new_group.id,
                        product_id=valid.product
                    )
                    session.add(new_product_link)
                    session.commit()
                    session.refresh(new_product_link)
                    product_link_status = {"message": "Product linked successfully"}
            else:
                product_link_status = {"message": "Product not defined"}

        return {"message": {"Category": category_link_status, "Product": product_link_status}}
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
 
# @In.put("/update-inheritance/")
# async def update_inheritance_group(
#     session: SessionDep,
#     current_user: UserDep,
#     tenant: str,
    
#     valid: TemplateView,
# ):
#     try:
#         if not check_permission(
#             session, "Update", role_modules['update'], current_user
#             ):
#             raise HTTPException(
#                 status_code=403, detail="You Do not have the required privilege"
#             )
         
#         # organization_ids = get_organization_ids_by_scope_group(session, current_user)
 
#         # inheritance_exist = session.exec(
#         #     select(db_model).where(db_model.organization.in_(organization_ids), db_model.id == valid.id)
#         # ).first()

#         selected_entry = session.exec(
#                 select(db_model).where(db_model.id == valid.id)
#             ).first()
        
#         if not selected_entry:
#             raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")
        
#         if valid.organization == organization_ids:
#             selected_entry.name = valid.name
#         else:
#             {"message": "invalid input select your own organization id"}    
 
#         # Commit the changes and refresh the object
#         session.add(valid)
#         session.commit()
#         session.refresh(valid)

#         return {"message": f"{endpoint_name} Updated successfully"}

#     except HTTPException as http_exc:
#         raise http_exc
#     except Exception:
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail="Something went wrong")


@In.put(endpoint['update'] + "/{group_id}")
async def update_inheritance_group(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    valid: TemplateView,
    
):
    try:
        if not check_permission(
            session, "Update",[ "Inheritance", "Administrative"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )  
         
        selected_entry = session.exec(
                select(db_model).where(db_model.id == valid.id)
            ).first()
        if not selected_entry:
            raise HTTPException(status_code=404, detail="Inheritance group not found")
        
        selected_entry.name = valid.name

        session.add(valid)
        session.commit()
        session.refresh(valid)

        return {"message": f"{endpoint_name} Updated successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")



@In.delete("/delete-inheritance/{inheritance_id}")
async def delete_inheritance_group(
    session: SessionDep,
    current_user: UserDep,
    inheritance_id: int, 
):
    try:
        # Check permission
        if not check_permission(
            session, "Delete", role_modules['delete'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        selected_entry = session.exec(
            select(db_model).where(db_model.id == inheritance_id)
        ).first()

        if not selected_entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")
        # Delete associated category links
        session.exec(
            delete(CategoryLink).where(CategoryLink.inheritance_group_id == inheritance_id)
        )
        # Delete associated product links
        session.exec(
            delete(ProductLink).where(ProductLink.inheritance_group_id == inheritance_id)
        )

        # Delete the inheritance group itself
        session.delete(selected_entry)
        session.commit()

        return {"message": f"{endpoint_name} deleted successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
