from typing import Annotated, List
from fastapi import APIRouter, HTTPException, Body, status, Depends
from models.MultiTenant import Company, Organization
from sqlmodel import select, Session
from db import get_session
from models.Users import User
from models.viewModel.multiTenantViewModel import TenantCreation

from utils.auth_util import get_current_user

TenantRouter =tr= APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]


@tr.get("/companies/")
async def get_organization(
    session: SessionDep,
) -> List[Organization]:
    """
    Retrieve all companies from the database.

    Args:
        session (SessionDep): Database session.

    Returns:
        List[Organization]: A list of Organization objects.
        If empty, it returns an empty list. []

    Raises:
        HTTPException: 400 if there is an error during retrieval.
    """
    try:
        # Query all organizations directly
        companies = session.exec(select(Company)).all()
        return companies
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
@tr.post("/create-company/")
async def create_company(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
    tenant: TenantCreation = Body(...),
) -> Company:

    try:
        existing_tenant = session.exec(select(Company).where(Company.company_name == tenant.company_name)).first()

        if existing_tenant is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company already registered",
            )
      #since the service provider is the one to create a tenant, the parent company would be the company of the service provider
        company = Company(
            id = None,
            company_name = tenant.company_name,
            owner_name = tenant.owner_name,
            description = tenant.description,
            logo_image = tenant.logo_image,
            parent_company_id = current_user['company']
        )
        session.add(company)
        session.commit()
        session.refresh(company)
        
        return company
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))           


@tr.get("/get-my-company/")
async def get_my_company(
    session: SessionDep,
    current_user: User = Depends(get_current_user),  # Extract the logged-in user
) -> dict:
    """
    Retrieve the company information for the logged-in user.

    Args:
        session (SessionDep): Database session.
        current_user (User): The currently logged-in user.

    Returns:
        dict: Company information including name, id, owner name, and logo image.

    Raises:
        HTTPException: 404 if the company is not found.
    """
    try:
        print(current_user);
        # Query the company associated with the logged-in user
        company = session.exec(select(Company).where(Company.id == current_user['company'])).first()

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found for the logged-in user",
            )

        # Return the company information
        return {
            "id": company.id,
            "company_name": company.company_name,
            "owner_name": company.owner_name,
            "logo_image": company.logo_image,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))