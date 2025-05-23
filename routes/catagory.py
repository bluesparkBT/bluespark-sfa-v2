from typing import Annotated, List, Dict, Any, Optional
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from utils.model_converter_util import get_html_types
from models.Product import Product, Category
from models.Inheritance import InheritanceGroup
from models.Account import ScopeGroup,ScopeGroupLink 
from utils.util_functions import validate_name
from models.Account import Organization
from utils.auth_util import get_current_user, check_permission
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_category_id_and_name, fetch_organization_id_and_name
import traceback


CatagoryRouter = c = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


@c.get("/get-categories")
def get_category(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,

):
    
    try: 
        print(current_user)
        if not check_permission(
            session, "Read",["Administrative", "Category"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )  
        # Fetch the inheritance group from the organization
        inherited_group_id = session.exec(
            select(Organization.inheritance_group).where(Organization.id == current_user.organization_id)
        ).first()
        test= session.exec(select(Organization.inheritance_group))
        print("test",test)
        print("inherited_group_id",inherited_group_id)
        inherited_group = session.exec(
            select(InheritanceGroup).where(InheritanceGroup.id == inherited_group_id)
        ).first()

        print("inherited_group",inherited_group)
        if inherited_group:
            inherited_categories = inherited_group.categories

            print("inherited_categories",inherited_categories)
        else:
            inherited_categories = []
        # Fetch products associated with the inheritance group

        
        # organization_ids = get_organization_ids_by_scope_group(session, current_user)
        scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == current_user.scope_group_id)).first()
        print ("scopgroup",scope_group)
   
        if scope_group != None:
            existing_orgs = [organization.id for organization in scope_group.organizations ]
        if scope_group == None:
            existing_orgs= []

        organization_categories = session.exec(
            select(Category).where(Category.organization_id.in_(existing_orgs))
        ).all()
        # categories = organization_group.categories

        organization_categories.extend(inherited_categories)

        category_list = []
        for category in organization_categories:
            category_temp = {
                "id": category.id,
                "Category Name": category.name,
                "Parent Category id": category.parent_category,
                "Parent Category name": category.parent_category,
                "UNSPC Code": category.code,
                "Description": category.description,
            }
            if category_temp not in category_list:
                category_list.append(category_temp)

        return category_list

    except Exception as e:
        traceback.print_exc()
  
    
@c.get("/get-category/{category_id}")
def get_category(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    category_id: int,
):
    try:
        if not check_permission(
            session, "Read",[ "Category", "Administrative"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        # Fetch categories based on organization IDs
        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        db_category = session.exec(
            select(Category).where(Category.organization_id.in_(organization_ids), Category.id == category_id)
        ).first()

        if not db_category:
            raise HTTPException(status_code=404, detail="Category not found")
        

        return db_category
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))  
    
@c.get("/category-form/")
def get_category_form(
    tenant: str,
    session: SessionDep,
    current_user: UserDep,
) :
    """   Retrieves the form structure for creating a new category.
    """
    try:
        # Check permission
        if not check_permission(
            session, "Create",["Administrative", "Category"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )   

          # This will display a list of category names

        form_structure = {
            "id": "",
            "name": "",
            "code": "",
            "description": "",
            "parent_category": fetch_category_id_and_name(session, current_user),
            "organization": fetch_organization_id_and_name(session, current_user),
        } 

        return {"data": form_structure, "html_types": get_html_types("category")}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@c.post("/create-category")
def create_category(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    name: str = Body(...),
    code: str = Body(...),
    description: str | None = Body(...),
    # parent_category: Optional [int] = Body(...),
    organization: str = Body(...)
):
    try:
        
        if not check_permission(
            session, "Create",[ "Catagory", "Administrative"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        db_category_code = session.exec(
            select(Category.code).where(Category.organization_id.in_(organization_ids), Category.code == code)
        ).first()
        # existing_category = session.exec(
        #             select(Category).where(Category.code == code)
        #         ).first()
        
        if db_category_code:
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
#            description=description,
            organization_id=int(organization),
            
            )
        session.add(new_category)
        session.commit()
        session.refresh(new_category)

        return new_category

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
 
# update a single category by ID
@c.put("/update-category/{category_id}")
def update_category(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    category_id: int,

    updated_code: str = Body(...),
    updated_name: str = Body(...),
    updated_description: str = Body(...),
    # updated_parent_category: int = Body(...),
    updated_organization: int = Body(...),
):
    try:
        # Check permission
        if not check_permission(
            session, "Update",[ "Catagory", "Administrative"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        # Fetch categories based on organization IDs
        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        selected_category = session.exec(
            select(Category).where(Category.organization_id.in_(organization_ids), Category.id == category_id)
        ).first()

        if not selected_category:
            raise HTTPException(status_code=404, detail="Category not found")


        # Validate the name if provided
        if updated_name is not None and not validate_name(updated_name):
            raise HTTPException(status_code=400, detail="Invalid category name format")

        # Check if a category with the same code exists (excluding the current category)
       
        selected_category.name = updated_name
        selected_category.code = updated_code
        selected_category.description = updated_description
        # selected_category.parent_category = updated_parent_category
        if updated_organization == organization_ids:
            selected_category.organization_id = updated_organization
        else:
            {"message": "invalid input select your owen organization id"}    
 
        # Commit the changes and refresh the object
        session.add(selected_category)
        session.commit()
        session.refresh(selected_category)

        return {"message": "Category Updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Delete a category by ID
@c.delete("/delete-category/{category_id}")
def delete_category(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    category_id: int,
) :
    try:
        # Check permission
        if not check_permission(
            session, "Delete",[ "Catagory", "Administrative"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        # Fetch categories based on organization IDs
        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        selected_category = session.exec(
            select(Category).where(Category.organization_id.in_(organization_ids), Category.id == category_id)
        ).first()

        if not selected_category:
            raise HTTPException(status_code=404, detail="Category not found")

    
        # Delete category after validation
        session.delete(selected_category)
        session.commit()

        return {"message": "Category deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))