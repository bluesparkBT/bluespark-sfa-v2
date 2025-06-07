from sqlmodel import select, Session, delete
from fastapi import APIRouter, Depends, HTTPException, Body, Path
from typing import Annotated, List, Dict, Any, Optional
from utils.auth_util import get_current_user, check_permission
from utils.form_db_fetch import add_category_link, add_product_link
from db import SECRET_KEY, get_session
from models.Account import Organization
from models.Product_Category import Product, Category,ProductLink, CategoryLink, RoleLink, InheritanceGroup, ClassificationLink, PointOfSaleLink
from models.viewModel.InheritanceView import InheritanceView as TemplateView , UpdateInheritanceView as UpdateTemplateView
from utils.model_converter_util import get_html_types
from utils.form_db_fetch import fetch_category_id_and_name, fetch_product_id_and_name, fetch_organization_id_and_name, fetch_role_id_and_name, get_organization_ids_by_scope_group
import traceback
from models import InheritanceGroup


InheritanceRouter =In= APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "inheritance"
db_model = InheritanceGroup

endpoint = {
    "get": f"/get-{endpoint_name}s",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",

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
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        db_entries = session.exec(
            select(db_model).where(db_model.organization.in_(organization_ids))
        ).all()

        if not db_entries:
            raise HTTPException(status_code=404, 
                detail=f"No {endpoint_name} Group created")
        inheritance_list = []
        for inheritance in db_entries:
            organization_name = session.exec(select(Organization.name).where(Organization.id == inheritance.organization)).first()
            temp = {
                "id": inheritance.id,
                "name": inheritance.name,
                "organization": organization_name,
                
            }
            if temp not in inheritance_list:
                inheritance_list.append(temp)
        return inheritance_list

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
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        db_entry = session.exec(
            select(db_model).where(db_model.id == id, db_model.organization.in_(organization_ids))
        ).first() 
        
        check_category_entry = session.exec(select(CategoryLink).where(CategoryLink.inheritance_group_id == id)).first()
        if check_category_entry:
            category_id = check_category_entry.id 
        else:
            category_id = "N/A" 
        check_product_entry = session.exec(select(ProductLink).where(ProductLink.inheritance_group_id == id)).first()
        if check_product_entry:
            product_id = check_product_entry.id
        else: 
            product_id = "N/A"
        check_role_entry = session.exec(select(RoleLink).where(RoleLink.inheritance_group_id == id)).first()
        if check_role_entry:
            role_id = check_role_entry.id
        else:
            role_id = "N/A"
        # check_classification_entry = session.exec(select(ClassificationLink).where(ClassificationLink.inheritance_group_id == id)).first()
        # check_pos_entry = session.exec(select(PointOfSaleLink).where(PointOfSaleLink.inheritance_group_id == id)).first()
                    

        if not db_entry:
            return {"message": f"{endpoint_name} not found"}

        return {
            "id": db_entry.id,
            "name": db_entry.name,
            "organization": db_entry.organization,
            "category": category_id,
            "product": product_id,
            "role": role_id,
            # "classification": "",
            # "point_of_sale": ""
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

@In.get(endpoint['get_form'])
def inheritance_form(
     tenant: str,
    session: SessionDep,
    current_user: UserDep,   
):
    try:
        if not check_permission(
            session, "Create",role_modules['get_form'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )      

        form_structure = {
            "id": "",
            "name": "",
            "organization": fetch_organization_id_and_name(session, current_user),
            "category": fetch_category_id_and_name(session, current_user) ,
            "product": fetch_product_id_and_name(session, current_user),
            "role": fetch_role_id_and_name(session, current_user),
            # "classification": fetch_classification_id_and_name(session, current_user),  
            # "point_of_sale": fetch_point_of_sale_id_and_name(session, current_user),
      
      } 

        return {"data": form_structure, "html_types": get_html_types("inheritance")}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

@In.post(endpoint['create'])
async def create_inheritance_group(             
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    valid: TemplateView
):
    try:
        if not check_permission(
            session, "Create", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        check_inheritance_exist = session.exec(
            select(db_model).where(db_model.name == valid.name, db_model.organization.in_(organization_ids))
        ).first()

        if check_inheritance_exist:
            raise HTTPException(status_code=400, detail=f"{endpoint_name} already exist")
        
        new_group = db_model(
            name=valid.name,
            organization = valid.organization
            )
        session.add(new_group)
        session.commit()

        # Category processing (only if provided)
        if valid.category:
            # existing_categories = session.exec(
            #     select(Category.id).where(Category.id.in_(valid.category))
            # ).all()
            # existing_category_ids = set(existing_categories)
            # invalid_ids = set(valid.category) - existing_category_ids
            # if invalid_ids:
            #     raise HTTPException(
            #         status_code=400,
            #         detail=f"Categories with IDs: {list(invalid_ids)} are not found"
            #     )
                
            for entry in valid.category:
                existing_link = session.exec(
                    select(CategoryLink).where(
                        CategoryLink.inheritance_group_id == new_group.id,
                        CategoryLink.category_id == entry
                    )
                ).first()
                if not existing_link:
                    new_link = CategoryLink(
                        inheritance_group_id=new_group.id,
                        category_id= entry
                    )
                    session.add(new_link)
                    session.commit()
                    session.refresh(new_link)

        # Product processing (only if provided)
        if valid.product:
            # existing_products = session.exec(
            #     select(Product.id).where(Product.id.in_(valid.product))
            # ).all()
            # existing_product_ids = set(existing_products)

            # invalid_ids = set(valid.category) - existing_product_ids
            # if invalid_ids:
            #     raise HTTPException(
            #         status_code=400,
            #         detail=f"Products with IDs: {list(invalid_ids)} are not found"
            #     )

            for entry in valid.product:
                existing_link = session.exec(
                    select(ProductLink).where(
                        ProductLink.inheritance_group_id == new_group.id,
                        ProductLink.product_id == entry
                    )
                ).first()
                if not existing_link:
                    new_link = ProductLink(
                        inheritance_group_id=new_group.id,
                        product_id= entry
                    )
                    session.add(new_link)
                    session.commit()
                    session.refresh(new_link)
        
        # Role processing (only if provided)
        if valid.role:
            # existing_roles = session.exec(
            #     select(Role.id).where(Role.id.in_(valid.role))
            # ).all()
            # existing_role_ids = set(existing_roles)
            # invalid_ids = set(valid.role) - existing_role_ids
            # if invalid_ids:
            #     raise HTTPException(
            #         status_code=400,
            #         detail=f"Roles with IDs: {list(invalid_ids)} are not found"
            #     )

            for entry in valid.category:
                existing_link = session.exec(
                    select(RoleLink).where(
                        RoleLink.inheritance_group_id == new_group.id,
                        RoleLink.role == entry
                    )
                ).first()
                if not existing_link:
                    new_link = RoleLink(
                        inheritance_group_id=new_group.id,
                        role= entry
                    )
                    session.add(new_link)
                    session.commit()
                    session.refresh(new_link)
        
        return {"message": f"{endpoint_name} successfully created"}
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


# @In.put(endpoint['update'] + "/{group_id}")
# async def update_inheritance_group(
#     session: SessionDep,
#     current_user: UserDep,
#     tenant: str,
#     valid: TemplateView,
    
# ):
#     try:
#         if not check_permission(
#             session, "Update",[ "Inheritance", "Administrative"], current_user
#             ):
#             raise HTTPException(
#                 status_code=403, detail="You Do not have the required privilege"
#             )  
         
#         selected_entry = session.exec(
#                 select(db_model).where(db_model.id == valid.id)
#             ).first()
#         if not selected_entry:
#             raise HTTPException(status_code=404, detail="Inheritance group not found")
        
#         selected_entry.name = valid.name

#         session.add(valid)
#         session.commit()
#         session.refresh(valid)

#         return {"message": f"{endpoint_name} Updated successfully"}

#     except HTTPException as http_exc:
#         raise http_exc
#     except Exception:
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail="Something went wrong")

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
