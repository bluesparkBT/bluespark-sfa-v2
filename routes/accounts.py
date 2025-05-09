from typing import Annotated, List
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Body, status, Depends
from sqlmodel import select, Session
from db import get_session
from models.Account import User, ScopeGroup, ScopeGroupLink, Organization, Gender
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
    
    if not user.organization or not user.organization:
        raise HTTPException(status_code=400, detail="User missing company or organization info")

    if not user or not verify_password(password+user.username, user.hashedPassword):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token_expires = timedelta(minutes=90)
    token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "company": user.company.id,
            "organization": user.organization.id,

            },
        expires_delta = access_token_expires,
    )
    
    return {"access_token": token}

@ar.post("/register-superadmin/")
async def create_superadmin_user(
    session: SessionDep,
      fullname: str = Body(...),
      username: str = Body(...),
      email: str = Body(...),
      password: str = Body(...),
      service_provider_company: str = Body(...),
):
    try:
        existing_superadmin = session.exec(select(User).where(User.username== username)).first()
        if existing_superadmin is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Superadmin already registered",
            )
        

        new_user =User(
            fullname=fullname,
            username=username,
            email=email,
            hashedPassword=get_password_hash(password + username),
        )
        
        
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        organization = Organization(
            organization_name=service_provider_company,
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
        
        scope_group_link = ScopeGroupLink(
            scope_group_id=scope_group.id,
            organization_id=organization.id,
        )
        
        session.add(scope_group_link)
        session.commit()
        session.refresh(scope_group_link)

        # Link the scope group to the company (or organization)

        return {"message": "Superadmin created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@ar.get("/get-my-user/")
async def get_my_user(
    session: SessionDep,
    user_id: int = Body(...),
):
    try:
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@ar.get("/get-users/")
async def get_users(
    session: SessionDep,
) -> List[User]:
    try:
        users = session.exec(select(User)).all()
        if not users:
            raise HTTPException(status_code=404, detail="No users found")
        return users
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@ar.delete("/delete-superadmin/")
async def delete_superadmin_user(
    session: SessionDep,
    super_admin_id: int = Body(...),
):
    try:
        superadmin = session.exec(select(User).where(User.id == super_admin_id)).first()
        if not superadmin:
            raise HTTPException(status_code=404, detail="Superadmin not found")

        session.delete(superadmin)
        session.commit()

        return {"message": "Superadmin deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
    
@ar.post("/create-user/")
async def create_user(
    session: SessionDep,
            fullname: str = Body(...),
            username: str = Body(...),
            password: str = Body(...), 
            email: str = Body(...),
            role_id: int = Body(...),
            scope: str = Body(...),
            scope_group_id: str = Body(...),
            organization: int = Body(...),
            phone_number: str = Body(...),
            gender: Gender = Body(...),
            salary: float = Body(...),
            position: str = Body(...),
            date_of_birth: str = Body(...),
            date_of_joining: str = Body(...),
            id_type: str = Body(...),
            id_number: str = Body(...),
            
):
    try: 
        existing_user = session.exec(select(User).where(User.username == username)).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        new_user = User(
            fullname=fullname,
            username=username,
            email=email,
            phone_number=phone_number,
            hashedPassword=get_password_hash(password + username),
            organization= organization,
            role_id=role_id,           
            gender=gender,
            salary=salary,
            position=position,
            date_of_birth=date_of_birth,
            date_of_joining=date_of_joining,
            id_type=id_type,
            id_number=id_number,
            scope=scope,
            scope_group_id=scope_group_id,

        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return {
            "message": "User: {new_user} registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))