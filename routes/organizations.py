from typing import Annotated, List
from fastapi import APIRouter, HTTPException, Body, status, Depends
from sqlmodel import select, Session
from db import get_session
from models.Account import User, Organization, OrganizationType

from utils.auth_util import get_current_user
from utils.util_functions import validate_name, validate_image

TenantRouter =tr= APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]


@tr.post("/create-organization/")
async def create_organization(
    session: SessionDep,
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
        
        if validate_name(organization_name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name is not valid",
        )
        elif validate_name(owner_name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Owner name is not valid",
        )
        elif validate_name(description) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Description is not valid",
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
        organization = session.exec(select(Organization).where(Organization.id == current_user.organization_id)).first()

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="organization not found for the logged-in user",
            )

        # Return the organization information
        return {
            "organization": organization.organization_name,
            "owner": organization.owner_name,
            "logo": organization.logo_image,
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@tr.get("/get-organizations/")
async def get_organizations(
    session: SessionDep,
) -> List[Organization]:
    """
    Retrieve all companies from the database.

    Args:
        session (SessionDep): Database session.

    Returns:
        List[Organizations]: A list of Organizations objects.
        If empty, it returns an empty list. []

    Raises:
        HTTPException: 400 if there is an error during retrieval.
    """
    try:
        # Query all companies directly
        organizations = session.exec(select(Organization)).all()
        
        organization_list = []
        
        for organization in organizations:
            organization_list.append({
                "organization": organization.organization_name,
                "owner": organization.owner_name,
                "logo": organization.logo_image,
            })
            
        return organization_list
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

    