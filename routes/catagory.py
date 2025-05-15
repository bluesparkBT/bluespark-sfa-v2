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

SessionDep = Annotated[Session, Depends(get_session)]

CatagoryRouter = tr = APIRouter()


# Create a new category
@tr.post("/create-category")
def create_category(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
    code: int = Body(...),
    parent_category: int = Body(...),
    name: str = Body(...),
    description: str = Body(...),
    organization: int = Body(...),

) -> Category:
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
@tr.get("/get-categories")
def get_categories(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> List[dict]:
    try:
        if not check_permission(
            session, "Read", "Catagory", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        organization_ids= get_organization_ids_by_scope_group(session, current_user)

        # Fetch categories based on organization IDs
        db_categories = session.exec(
            select(Category).where(Category.organization_id.in_(organization_ids))
        ).all()


        # Validate retrieved categories
        if not db_categories:
            raise HTTPException(status_code=404, detail="No categories found")
        
        catagory_list = []
        
        for db_category in db_categories:
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
    
@tr.get("/get-category/{category_id}")
def get_category(
    category_id: int,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
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
@tr.put("/update-category")
def update_category(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
    category_id: int = Body(...),
    updated_code: int = Body(...),
    updated_name: str = Body(...),
    updated_description: str = Body(...),
    updated_parent_category: Optional[int] = Body(None),
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
@tr.delete("/archive-category/{category_id}")
def delete_category(
    category_id: int,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
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