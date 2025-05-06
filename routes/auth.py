from typing import Optional
from fastapi import APIRouter, HTTPException, Body, status, Depends
from models.multitenant import Company, Organization, OrganizationType
from sqlmodel import select, Session
from db import get_session
from models.user import User,SuperAdminUser, ScopeGroup, Scope, ScopeGroupOrganizationLink
from utils.auth_util import verify_password, create_access_token, get_password_hash

AuthenticationRouter =ar= APIRouter()

@ar.post("/login/")
def login(
    session: Session = Depends(get_session),
    username: str = Body(...),
    password: str = Body(...)
):
    user = session.exec(select(SuperAdminUser).where(SuperAdminUser.username == username)).first()
    print(user);
    if not user or not verify_password(password+user.username, user.hashedPassword):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(data={"sub": user.username})
    return {"access_token": token}


@ar.post("/register-superadmin/")
async def create_superadmin_user(
    session: Session = Depends(get_session),
    username: str = Body(...),
    password: str = Body(...),
    email: Optional[str] = Body(None),
    service_provider_company: str = Body(...)
):
    try:
        organization = Organization(
            organization_name=service_provider_company,
            organization_type = OrganizationType.company

        )
        session.add(organization)
        session.commit()
        session.refresh(organization)

        scope_group = ScopeGroup(
           scope_name="Superadmin scope",
        )

        session.add(scope_group)
        session.commit()
        session.refresh(scope_group)

        scope_organization_link = ScopeGroupOrganizationLink(
            scope_group_id=scope_group.id,
            organization_id=organization.id
        )

        session.add(scope_organization_link)
        session.commit()
        session.refresh(scope_organization_link)



        user = SuperAdminUser(
            id=None,
            username=username,
            email=email,
            service_provider_company = organization.id,
            hashedPassword=get_password_hash(password + username),
            scope_group_id=scope_group.id
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@ar.post("/register/")
def register(
    session: Session = Depends(get_session),
    username: str = Body(...),
    email: str = Body(...),
    password: str = Body(...)
):
    # Check if user already exists
    existing_user = session.exec(select(User).where(User.username == username)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Hash the password
    hashed_password = get_password_hash(password)

    # Create user
    new_user = User(username=username, email=email, passhash=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    # Optionally return access token
    token = create_access_token(data={"sub": new_user.username})
    return {
        "message": "User registered successfully",
        "access_token": token
    }
