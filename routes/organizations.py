from typing import Annotated, List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body, status, Depends, Path
from sqlmodel import select, Session
from sqlalchemy.orm import selectinload
from db import get_session
from models.Account import User, Organization, OrganizationType, ScopeGroup, Scope, Role, ScopeGroupLink
from utils.auth_util import get_tenant, get_current_user, check_permission
from utils.model_converter_util import get_html_types
from utils.util_functions import validate_name, validate_image
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_organization_id_and_name
import traceback

TenantRouter =tr= APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

@tr.get("/get-organizations/")
async def get_organizations(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str,

):
    """
    Retrieve all organizations with their associated scope groups.
    """
    try:
        if not check_permission(
            session, "Read", "Organization", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        organizations = session.exec(select(Organization).where(Organization.id.in_(organization_ids)))

        if not organizations:
            raise HTTPException(status_code=404, detail="No organizations found")

        organization_list = []

        for org in organizations:
            organization_list.append({
                "id": org.id,
                "organization": org.organization_name,
                "owner": org.owner_name,
                "logo": org.logo_image,
                "description": org.description,
                "organization_type": org.organization_type,
                "inheritance_group": org.inheritance_group,
                "parent_organization": org.parent_id,
                "scope_groups": [
                    {"id": sg.id, "scope_name": sg.scope_name}
                    for sg in org.scope_groups
                ]
            })

        return organization_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@tr.get("/get-my-organization/")
async def get_my_organization(
    session: SessionDep,
    tenant: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Retrieve the organization information for the logged-in user.

    Args:
        session (SessionDep): Database session.
        current_user (User): The currently logged-in user.

    Returns:
        dict: organization information including name, id, owner name, and logo image.

    Raises:
        HTTPException: 404 if the organization is not found.
    """
    try:
        if not check_permission(
            session, "Read", ["Organization", "Administrative"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        organization = session.exec(select(Organization).where(Organization.id == current_user.organization_id)).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="organization not found for the logged-in user",
            )

        # Return the organization information
        return {
            "id": organization.id,
            "organization": organization.organization_name,
            "owner": organization.owner_name,
            "logo": organization.logo_image,
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@tr.get("/get-organization/{id}")
async def get_organization(
    session: SessionDep,
    id: int,
    current_user: UserDep,
    tenant: str,
):
    try:
        if not check_permission(
            session, "Read", "Organization", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        organization = session.exec(select(Organization).where(Organization.id == id)).first()
        if not organization:
            raise HTTPException(status_code=404, detail="Role not found")
  
        return {
            "id": organization.id,
            "organization_name": organization.organization_name,
            "description": organization.description,
            "owner_name": organization.owner_name,
            "logo_image": organization.logo_image,
            "organization_type": organization.organization_type,
            "parent_organization": organization.parent_id
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
     
@tr.get("/organization-form/")
async def get_form_fields_organization(
    session: SessionDep,
    tenant: str,
    current_user: UserDep
):

    try:
        if not check_permission(
            session, "Read", "Organization", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        organization_data = {
            "id": "",
            "organization_name": "",
            "owner_name": "",
            "description": "",
            "logo_image": "",
            "parent_organization": fetch_organization_id_and_name(session, current_user),
            "organization_type" : {i.value: i.value for i in OrganizationType}
            }
        

        return {"data": organization_data, "html_types": get_html_types('organization')}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@tr.post("/create-organization/")
async def create_organization(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    organization_name: str = Body(...),
    owner_name: str = Body(...),
    description: str = Body(...),
    logo_image: str = Body(...),
    parent_organization : int = Body(...),
    organization_type: str = Body(...),    
):

    try:
        if not check_permission(
            session, "Create", "Organization", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        existing_tenant = session.exec(select(Organization).where(Organization.organization_name == organization_name)).first()

        if existing_tenant is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company already registered",
        )
        #Check Validity
        if validate_name(owner_name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company owner name is not valid",
        )
        elif validate_image(logo_image) == False and logo_image is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Logo image is not valid",
        )
        
        organization = Organization(
            id = None,
            organization_name = organization_name,
            owner_name = owner_name,
            description = description,
            logo_image = logo_image,
            parent_id = parent_organization,
            organization_type = organization_type
        )
        
        
        session.add(organization)
        session.commit()
        session.refresh(organization)
        
    
        # Link the System Admin ScopeGroup to the tenant organization
        scope_group_link = ScopeGroupLink(
            scope_group_id=current_user.scope_group_id,
            organization_id=organization.id,
        )
        session.add(scope_group_link)
        session.commit()

        return {"message": "Organization created successfully", "organization": organization_name}
    
    except Exception as e:
        traceback.print_exc()
        
        raise HTTPException(status_code=400, detail=str(e))           

@tr.put("/update-organization/")
async def create_organization(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str,

    id: int = Body(...),
    organization_name: str = Body(...),
    owner_name: str = Body(...),
    description: str = Body(...),
    logo_image: str = Body(...),
    inheritance_group: int | str = Body(...),
    organization_type: str = Body(...),    
    parent_organization: int | str = Body(...)
):

    try:
        if not check_permission(
            session, "Update", "Organization", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        existing_tenant = session.exec(select(Organization).where(Organization.id == id)).first()
        if existing_tenant is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization not found",
        )
        #Check Validity
        
        if validate_name(owner_name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company owner name is not valid",
        )
        elif validate_image(logo_image) == False and logo_image is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Logo image is not valid",
        )

        existing_tenant.organization_name = organization_name
        existing_tenant.owner_name = owner_name
        existing_tenant.description = description
        if inheritance_group:
            existing_tenant.inheritance_group= inheritance_group
        existing_tenant.logo_image = logo_image
        existing_tenant.organization_type = organization_type
        if parent_organization:
            existing_tenant.parent_id = parent_organization
            
        session.add(existing_tenant)
        session.commit()
        session.refresh(existing_tenant)
        
        return {"message": "Organization updated successfully", "organization": organization_name}
    
    except Exception as e:
        traceback.print_exc()
        
        raise HTTPException(status_code=400, detail=str(e)) 

@tr.delete("/delete-organization/{id}")
async def delete_organization(
    session: SessionDep,
    current_user: UserDep,
    id: int,    
    tenant: str,
):
    """
    Delete an organization by ID.

    Args:
        session (SessionDep): Database session.
        id (int): ID of the organization to delete.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException: 404 if the organization is not found.
    """
    try:
        if not check_permission(
            session, "Delete", "Organization", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        organization = session.get(Organization, id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        # Delete the organization
        session.delete(organization)
        session.commit()

        return {"message": "Organization deleted successfully"}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

# @ar.get("/get-organization-hierarchy/")
# async def get_organization_hierarchy(
#     session: SessionDep,
# tenant: str,
#     current_user: UserDep,
#     scope_group_id: int = Body(...),
# ):
#     try:
#         if not check_permission(
#             session, "Read", "Organization", current_user
#             ):
#             raise HTTPException(
#                 status_code=403, detail="You Do not have the required privilege"
#             )
#         scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == scope_group_id)).first()
#         if not scope_group:
#             raise HTTPException(status_code=404, detail="Scope group not found")

#         hierarchy = get_hierarchy(scope_group, session)
        
#         return {
#             "scope_group": scope_group.scope_name,
#             "hierarchy": hierarchy
#         }
#     except Exception as e:
traceback.print_exc()
#         raise HTTPException(status_code=400, detail=str(e))
    
