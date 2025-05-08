from typing import Annotated
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Body, status, Depends
from models.MultiTenant import Company
from sqlmodel import select, Session
from db import get_session
from models.Users import User
from models.MultiTenant import ScopeGroup, ScopeGroupOrganizationLink
from models.viewModel.authViewModel import UserCreation, SuperAdminUserCreation

from utils.auth_util import verify_password, create_access_token, get_password_hash

AuthenticationRouter =ar= APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]


@ar.post("/login/")
def login(
    session: SessionDep,
    username: str = Body(...),
    password: str = Body(...)
):
    user = session.exec(select(User).where(User.username == username)).first()
    
    if not user.company_id and not user.organization_id:
        raise HTTPException(status_code=400, detail="User missing company or organization info")

    if not user or not verify_password(password+user.username, user.hashedPassword):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token_expires = timedelta(minutes=90)
    token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "company": user.company_id,
            "organization": user.organization_id,
            },
        expires_delta = access_token_expires,
    )
    
    return {"access_token": token}

@ar.post("/register-superadmin/")
async def create_superadmin_user(
    session: SessionDep,
    super_admin: SuperAdminUserCreation = Body(...),
):
    try:
        existing_superadmin = session.exec(select(User)).first()
        if existing_superadmin is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Superadmin already registered",
            )

    

        company = Company(
            company_name=super_admin.service_provider_company,
        )
        session.add(company)
        session.commit()
        session.refresh(company)

        scope_group = ScopeGroup(
            scope_name="Superadmin scope",
            company_id=company.id,
        )
        session.add(scope_group)
        session.commit()
        session.refresh(scope_group)

        user = User(
            id=None,
            fullname=super_admin.fullname,
            username=super_admin.username,
            email=super_admin.email,
            hashedPassword=get_password_hash(super_admin.password + super_admin.username),
            company_id = company.id
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Link the scope group to the company (or organization)
        scope_organization_link = ScopeGroupOrganizationLink(
            scope_group_id=scope_group.id,
            organization_id=None,
            company_id=company.id,
        )
        session.add(scope_organization_link)
        session.commit()
        session.refresh(scope_organization_link)

        return {"message": "Superadmin created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
@ar.post("/create-user/")
async def create_user(
    session: SessionDep,
    user_data: UserCreation = Body(...),
):
    try: 
        existing_user = session.exec(select(User).where(User.username == user_data.username)).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
        

        new_user = User(
            fullname=user_data.fullname,
            username=user_data.username,
            email=user_data.email,
            phone=user_data.phone_number,
            hashedPassword=get_password_hash(user_data.password + user_data.username),
            gender=user_data.gender,
            salary=user_data.salary,
            position=user_data.position,
            date_of_birth=user_data.date_of_birth,
            date_of_joining=user_data.date_of_joining,
            id_type=user_data.id_type,
            id_number=user_data.id_number,
            scope=user_data.scope,
            scope_group_id=None,
            organization_id= user_data.organization,
            company_id= user_data.company,

        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return {
            "message": "User: {new_user} registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))