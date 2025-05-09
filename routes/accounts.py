from typing import Annotated, List
from datetime import timedelta, date, datetime
from fastapi import APIRouter, HTTPException, Body, status, Depends
from sqlmodel import select, Session
from db import get_session
from models.Account import User, ScopeGroup, ScopeGroupLink, Organization, Gender, Scope
from utils.auth_util import verify_password, create_access_token, get_password_hash
from utils.util_functions import validate_name, validate_email, validate_phone_number

AuthenticationRouter =ar= APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]


@ar.post("/login/")
def login(
    session: SessionDep,
    username: str = Body(...),
    password: str = Body(...)
):
    
    try:
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
                "organization": user.organization,
                },
            expires_delta = access_token_expires,
        )
        
        return {"access_token": token}
    
    except Exception as e:
        return {"error": str(e)}
    
@ar.get("/get-my-user/")
async def get_my_user(
    session: SessionDep,
    user_id: int = Body(...),
):
    try:
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "id": user.id,
            "fullname": user.fullname,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "organization": user.organization,
            "role_id": user.role_id,
            "manager_id": user.manager_id,
            "scope": user.scope,
            "scope_group_id": user.scope_group_id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@ar.post("/create-superadmin/")
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
        
        organization = Organization(
            organization_name=service_provider_company,
        )
        session.add(organization)
        session.commit()
        session.refresh(organization)
        
        new_user =User(
            fullname=fullname,
            username=username,
            email=email,
            hashedPassword=get_password_hash(password + username),
            organization= organization.id,
        )
        
        
        session.add(new_user)
        session.commit()
        session.refresh(new_user)



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
    
@ar.get("/get-users/")
async def get_users(
    session: SessionDep,
):
    try:
        users = session.exec(select(User)).all()
        if not users:
            raise HTTPException(status_code=404, detail="No users found")
        
        user_list = []
        
        for user in users:
            user_list.append({
                "id": user.id,
                "fullname": user.fullname,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "organization": user.organization,
                "role_id": user.role_id,
                "manager_id": user.manager_id,
                "scope": user.scope,
                "scope_group_id": user.scope_group_id,
            })
            
        return user_list

        
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
            scope: Scope = Body(...),
            scope_group_id: int = Body(...),
            organization: int = Body(...),
            phone_number: str = Body(...),
            gender: Gender = Body(...),
            salary: float = Body(...),
            position: str = Body(...),
            date_of_birth: datetime = Body(...),
            date_of_joining: datetime = Body(...),
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
        #check input validity
        if validate_name(fullname) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fullname is not valid",
        )

        elif validate_email(email) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is not valid",
        )
        elif validate_phone_number(phone_number) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is not valid",
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

@ar.put("/update-user/")
async def update_uer(
    session: SessionDep,
            fullname: str = Body(...),
            username: str = Body(...),
            password: str = Body(...), 
            email: str = Body(...),
            role_id: int = Body(...),
            scope: Scope = Body(...),
            scope_group_id: str = Body(...),
            organization: int = Body(...),
            phone_number: str = Body(...),
            gender: Gender = Body(...),
            salary: float = Body(...),
            position: str = Body(...),
            date_of_birth: datetime = Body(...),
            date_of_joining: datetime = Body(...),
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
        #check input validity
        if validate_name(fullname) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fullname is not valid",
        )
        elif validate_email(email) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is not valid",
        )
        elif validate_phone_number(phone_number) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is not valid",
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

@ar.delete("/delete-user/")
async def delete_user(
    session: SessionDep,
    user_id: int = Body(...),
):
    try:
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        session.delete(user)
        session.commit()

        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@ar.post("/create-scope-group/")
async def create_scope_group(
    session: SessionDep,
    scope_name: str = Body(...),
    organization_ids: List[int] = Body(...),
):
    try:
        existing_scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.scope_name == scope_name)).first()
        if existing_scope_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scope group already exists",
            )

        # Add related organizations
        organizations = session.exec(select(Organization).where(Organization.id.in_(organization_ids))).all()
        if not organizations:
            raise HTTPException(status_code=400, detail="Invalid organization IDs")
                
        scope_group = ScopeGroup(
            scope_name=scope_name,
        )
        
        scope_group.organizations = organizations
        
        session.add(scope_group)
        session.commit()
        session.refresh(scope_group)

        return {
            "message": "Scope group", scope_group.scope_name: "created successfully",
            "organizations": [org.organization_name for org in scope_group.organizations]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@ar.get("/get-scope-groups/")
async def get_scope_groups(
    session: SessionDep,
):
    try:
        scope_groups = session.exec(select(ScopeGroup)).all()
        if not scope_groups:
            raise HTTPException(status_code=404, detail="No scope groups found")
        
        scope_group_list = []
        
        for scope_group in scope_groups:
            scope_group_list.append({
                "id": scope_group.id,
                "scope_name": scope_group.scope_name,
                "organizations": [org.organization_name for org in scope_group.organizations],
            })
            
        return scope_group_list

        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@ar.delete("/delete-scope-group/")
async def delete_scope_group(
    session: SessionDep,
    scope_group_id: int = Body(...),
):
    try:
        scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == scope_group_id)).first()
        if not scope_group:
            raise HTTPException(status_code=404, detail="Scope group not found")

        session.delete(scope_group)
        session.commit()

        return {"message": "Scope group deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

# @ar.get("/get-organization-hierarchy/")
# async def get_organization_hierarchy(
#     session: SessionDep,
#     scope_group_id: int = Body(...),
# ):
#     try:
#         scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == scope_group_id)).first()
#         if not scope_group:
#             raise HTTPException(status_code=404, detail="Scope group not found")

#         hierarchy = get_hierarchy(scope_group, session)
        
#         return {
#             "scope_group": scope_group.scope_name,
#             "hierarchy": hierarchy
#         }
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))
    

