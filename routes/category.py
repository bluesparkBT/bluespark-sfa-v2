from typing import Annotated, List, Dict, Any, Optional, Union
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from utils.model_converter_util import get_html_types
from models.Product_Category import Product, Category, InheritanceGroup
from models.Account import ScopeGroup,ScopeGroupLink 
from utils.util_functions import validate_name
from models.viewModel.CategoryView import CategoryView as TemplateView
from models.Account import Organization
from utils.auth_util import get_current_user, check_permission, check_permission_and_scope
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_category_id_and_name, fetch_organization_id_and_name, fetch_id_and_name
import traceback


endpoint_name = "category"

endpoint = {
    "get": f"/get-{endpoint_name}",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",
    "update": f"/update-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}

role_modules = {   
    "get": ["Administrative", "Category"],
    "get_form": ["Administrative", "Category"],
    "create": ["Administrative", "Category"],
    "update": ["Administrative", "Category"],
    "delete": ["Administrative", "Category"],
}

CategoryRouter = c = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

UserDep = Annotated[dict, Depends(get_current_user)]

@c.get(endpoint['get'])
def get_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str

):
    
    try:  
        orgs_in_scope = check_permission_and_scope(session, "Read", role_modules['get'], current_user)
        
        inherited_group_id = session.exec(
            select(Organization.inheritance_group).where(Organization.id == current_user.organization)
        ).first()
        
        inherited_group = session.exec(
            select(InheritanceGroup).where(InheritanceGroup.id == inherited_group_id)
        ).first()

        if inherited_group:
            inherited_categories = inherited_group.categories

        else:
            inherited_categories = []
        
        # organization_ids = get_organization_ids_by_scope_group(session, current_user)
        # scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == current_user.scope_group)).first()
   
        # if scope_group != None:
        #     existing_orgs = [organization.id for organization in scope_group.organizations ]
        # if scope_group == None:
        #     existing_orgs= []

        categories = session.exec(
            select(Category).where(Category.organization.in_(orgs_in_scope["organization_ids"]))
        ).all()
        # categories = organization_group.categories

        categories.extend(inherited_categories)

        category_list = []
        for category in categories:
            category_temp = {
                "id": category.id,
                "Category Name": category.name,
                "Parent Category": category.parent_category,
                "UNSPC Code": category.code,
                "description": category.description,
            }
            if category_temp not in category_list:
                category_list.append(category_temp)

        return category_list

    except Exception as e:
        traceback.print_exc()
 
@c.get(endpoint['get_by_id'] + "/{id}")
def get_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int,
    # valid: TemplateView,
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
            select(Category).where(Category.organization.in_(organization_ids), Category.id == id)
        ).first()

        if not db_category:
            raise HTTPException(status_code=404, detail="Category not found")
        

        return db_category
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@c.get(endpoint['get_form'])
def get_template_form(
    tenant: str,
    session: SessionDep,
    current_user: UserDep,
) :
    """   Retrieves the form structure for creating a new category.
    """
    try:
        # Check permission
        if not check_permission(
            session, "Create",role_modules['get_form'], current_user
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

@c.post(endpoint['create'])
def create_template(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    valid: TemplateView,
):
    try:
        
        if not check_permission(
            session, "Create", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        # Create a new category entry from validated input
        new_category = Category.model_validate(valid)
        session.add(new_category)
        session.commit()
        session.refresh(new_category)

        return new_category

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
 
# update a single category by ID
@c.put(endpoint['update'])
def update_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
   
    valid: TemplateView,
):
    try:
        # Check permission
        if not check_permission(
            session, "Update",role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        # Fetch categories based on organization IDs
        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        selected_category = session.exec(
            select(Category).where(Category.organization.in_(organization_ids), Category.id == valid.id)
        ).first()

        if not selected_category:
            raise HTTPException(status_code=404, detail="Category not found")


       
       
        selected_category.name = valid.name
        selected_category.code = valid.code
        selected_category.parent_category = valid.parent_category

        
        selected_category.description = valid.description
        if valid.organization == organization_ids:
            selected_category.organization = valid.organization
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
@c.delete(endpoint['delete']+ "/{id}")
def delete_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int
) :
    try:
        # Check permission
        if not check_permission(
            session, "Delete",role_modules['delete'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        # Fetch categories based on organization IDs
        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        selected_category = session.exec(
            select(Category).where(Category.organization.in_(organization_ids), Category.id == id)
        ).first()

        if not selected_category:
            raise HTTPException(status_code=404, detail="Category not found")

    
        # Delete category after validation
        session.delete(selected_category)
        session.commit()

        return {"message": "Category deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
