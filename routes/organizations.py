from typing import Annotated, List
from fastapi import APIRouter, HTTPException, Body, status, Depends
from sqlmodel import select, Session
from sqlalchemy.orm import selectinload
from db import get_session
from models.Account import User, Organization, OrganizationType, ScopeGroup

from utils.auth_util import get_current_user
from utils.util_functions import validate_name, validate_image

TenantRouter =tr= APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


@tr.post("/create-organization/")
async def create_organization(
    session: SessionDep,
    current_user: UserDep,
    organization_name: str = Body(...),
    owner_name: str = Body(...),
    description: str = Body(...),
    logo_image: str = Body(...),
    organization_type: str = Body(...),    
):

    try:
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
            organization_name = organization_name,
            owner_name = owner_name,
            description = description,
            logo_image = logo_image,
            organization_type = organization_type
        )
        
        
        session.add(organization)
        session.commit()
        session.refresh(organization)
        
        return {"message": "Organization created successfully", "organization": organization_name}
    
    except Exception as e:
        
        raise HTTPException(status_code=400, detail=str(e))           


@tr.get("/get-my-organization/")
async def get_my_organization(
    session: SessionDep,
    current_user: User = Depends(get_current_user),  # Extract the logged-in user
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
        # Query the organization associated with the logged-in user
        organization = session.exec(select(Organization).where(Organization.id == current_user.get(organization))).first()

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
        raise HTTPException(status_code=400, detail=str(e))
@tr.get("/get-organizations/")
async def get_organizations(
    session: SessionDep,
):
    """
    Retrieve all organizations with their associated scope groups.
    """
    try:
        # Use selectinload to eagerly load the relationship
        sgo = select(Organization).options(selectinload(Organization.scope_groups))
        organizations = session.exec(sgo).all()

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
                "parent_organization": org.parent_id,
                "scope_groups": [
                    {"id": sg.id, "scope_name": sg.scope_name}
                    for sg in org.scope_groups
                ]
            })

        return organization_list

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@tr.delete("/delete-organization/{id}")
async def delete_organization(
    session: SessionDep,
    id: int,
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
        # Query the organization by ID
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
        raise HTTPException(status_code=400, detail=str(e))