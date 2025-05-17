from typing import Annotated, List, Dict, Any, Optional
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from utils.model_converter_util import get_html_types
from models.Product import Product, Category
from utils.util_functions import validate_name
from models.Account import User, AccessPolicy, Organization, OrganizationType, ScopeGroup, Scope, Role, ScopeGroupLink
from utils.auth_util import get_current_user, check_permission
from utils.get_hierarchy import get_organization_ids_by_scope_group
from models.Account import Organization
from utils.form_db_fetch import fetch_category_id_and_name, fetch_category_name

import traceback


CatagoryRouter = c = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]



@c.get("/Category-form/")
def get_category_form(
    tenant: str,
    category: Category ,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) :
    """   Retrieves the form structure for creating a new category.
    """
    try:
        # Check permission
        if not check_permission(
            session, "Create", "Category", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )   
        # Define the form structure
        
        category_data = fetch_category_id_and_name(session)

        # Extract only category names
        category_names = list(category_data.values())

          # This will display a list of category names

        form_structure = {
            "id": "",
            "code": "",
            "description": "",
            "image": "",
            "parent_category": category_names,
            # "products": "",
        } 

        return {"data": form_structure, "html_types": get_html_types("category")}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    

#get inheritance group  
@c.get("/get-categories")
def get_category(
        session: SessionDep,
        organization_id: int,
        current_user: User = Depends(get_current_user),

):
    
    try: 
        # Fetch the inheritance group from the organization
        inherited_group = session.exec(
            select(Organization.inheritance_group).where(Organization.id == current_user.organization_id)
        ).first()
        if inherited_group:

            inherited_categories = inherited_group.categories
        else:
            inherited_categories = []
        # Fetch products associated with the inheritance group
        organization_categories = session.exec(
            select(Category).where(Category.organization_id == current_user.organization_id)
        ).all()
        # categories = organization_group.categories

        organization_categories.extend(inherited_categories)

        new_category_list = []
        for category in organization_categories:
            new_category_list.append({
                "id": category.id,
                "Category Name": category.name,
                "Parent Category id": category.parent_category,
                "Parent Category name": category.parent_category,
                "UNSPC Code": category.code,
                "Description": category.description,
            })


    #      inherited_categories = inherited_group.categories

    #     # Fetch products associated with the inheritance group
    #     categories = session.exec(
    #         select(Category).where(Category.organization_id == current_user.organization_id)
    #     ).all()
    #     # categories = organization_group.categories
    #     All_categories = categories + P_categories

    #     return All_categories

    #     return 
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    




# Create a new category
@c.post("/create-category")
def create_category(
    session: SessionDep,
    tenant: str,
    current_user: User = Depends(get_current_user),
    code: int = Body(...),
    parent_category: int | str = Body(...),
    name: str = Body(...),
    description: str = Body(...),
    organization: int = Body(...)
):
    try:
        if not check_permission(
            session, "Create", "Catagory", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        existing_category = session.exec(
                    select(Category).where(Category.code == code)
                ).first()
        
        if existing_category:
            raise HTTPException(status_code=400, detail="Category with this code already exists")
       

        # Validate the name
        if not validate_name(name):
            raise HTTPException(status_code=400, detail="Invalid category name format")

        # Validate the description
        if not validate_name(description):
            raise HTTPException(status_code=400, detail="Invalid category description format")
        
        # Create a new category entry from validated input
        new_category = Category(
            code=code, 
            name=name, 
            parent_category=parent_category,
            description=description,
            organization_id=organization,
            
            )
        session.add(new_category)
        session.commit()
        session.refresh(new_category)

        return new_category

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get all categories
# @c.get("/get-categories")
# def get_categories(
#     session: SessionDep, 
#     current_user: UserDep,
#     tenant: str,
# ) -> List[dict]:
#     try:
#         if not check_permission(
#             session, "Read", "Catagory", current_user
#             ):
#             raise HTTPException(
#                 status_code=403, detail="You Do not have the required privilege"
#             )

#         organization_ids= get_organization_ids_by_scope_group(session, current_user)

#         # Fetch categories based on organization IDs
#         db_categories = session.exec(
#             select(Category).where(Category.organization_id.in_(organization_ids))
#         ).all()


#         # Validate retrieved categories
#         if not db_categories:
#             raise HTTPException(status_code=404, detail="No categories found")
        
#         catagory_list = []
        
#         for db_category in db_categories:
#             catagory_list.append({
#                 "id": db_category.id,
#                 "Category Name": db_category.name,
#                 "Parent Category": db_category.parent_category,
#                 "UNSPC Code": db_category.code,
#                 "Description": db_category.description,
#             })

#         return catagory_list

#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))
    
@c.get("/get-category/{category_id}")
def get_category(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    category_id: int,
) -> Category:
    try:
        if not check_permission(
            session, "Read", "Catagory", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        
        # Fetch categories based on organization IDs
        db_category = session.exec(
            select(Category).where(Category.id == category_id)
        ).first()
        # Retrieve the category

        if not db_category:
            raise HTTPException(status_code=404, detail="Category not found")
        catagory_list = []
        

        catagory_list.append({
            "id": db_category.id,
            "Category Name": db_category.name,
            "Parent Category": db_category.parent_category,
            "UNSPC Code": db_category.code,
            "Description": db_category.description,
        })

        return catagory_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))  
    
# update a single category by ID
@c.put("/update-category-{category_id}")
def update_category(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    category_id: int,

    updated_code: int = Body(...),
    updated_name: str = Body(...),
    updated_description: str = Body(...),
    updated_parent_category: int = Body(...),
    updated_organization: int = Body(...),
) -> Category:
    try:
        # Check permission
        if not check_permission(
            session, "Update", "Catagory", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )


        # Fetch categories based on organization IDs
        selected_category = session.exec(
            select(Category).where(Category.id == category_id)
        ).first()

        if not selected_category:
            raise HTTPException(status_code=404, detail="Category not found")


        # Validate the name if provided
        if updated_name is not None and not validate_name(updated_name):
            raise HTTPException(status_code=400, detail="Invalid category name format")

        # Validate the description if provided
        if updated_description is not None and not validate_name(updated_description):
            raise HTTPException(status_code=400, detail="Invalid category description format")
       
        # Check if a category with the same code exists (excluding the current category)
       
        selected_category.name = updated_name
        selected_category.code = updated_code
        selected_category.description = updated_description
        selected_category.parent_category = updated_parent_category
        selected_category.organization_id = updated_organization
 
        # Commit the changes and refresh the object
        session.add(selected_category)
        session.commit()
        session.refresh(selected_category)

        return {
           "message": "Category updated successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Delete a category by ID
@c.delete("/archive-category/{category_id}")
def delete_category(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    category_id: int,
) :
    try:
        # Check permission
        if not check_permission(
            session, "Delete", "Catagory", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )


        # Fetch categories based on organization IDs
        db_category = session.exec(
            select(Category).where(Category.id == category_id)
        ).first()
        # Retrieve the category

        if not db_category:
            raise HTTPException(status_code=404, detail="Category not found")
    
        # Delete category after validation
        session.delete(db_category)
        session.commit()

        return {"message": "Category deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))