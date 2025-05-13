
from typing import Annotated, List, Dict, Any
from datetime import timedelta, date, datetime
from fastapi import APIRouter, HTTPException, Body, status, Depends, Path
from sqlmodel import select, Session
from db import get_session
from models.Account import User, ScopeGroup, ScopeGroupLink, Organization, Gender, Scope, Role, AccessPolicy
from utils.auth_util import verify_password, create_access_token, get_password_hash
from utils.util_functions import validate_name, validate_email, validate_phone_number
from utils.auth_util import get_tenant, get_current_user, check_permission, generate_random_password
from utils.model_converter_util import get_html_types
from utils.form_db_fetch import fetch_organization_id_and_name


ServiceProvider =sp= APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

@sp.post("/login/")
def login(
    session: SessionDep,
    
    username: str = Body(...),
    password: str = Body(...)
):
    

    try:
        user = session.exec(select(User).where(User.username == username)).first()
        print(user)
        
        if not user and not user.organization_id:
            raise HTTPException(status_code=400, detail="User missing company or organization info")

        if not user or not verify_password(password+user.username, user.hashedPassword):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        access_token_expires = timedelta(minutes=90)
        token = create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "organization": user.organization_id,
                },
            expires_delta = access_token_expires,
        )
        
        return {"access_token": token}
    
    except Exception as e:
        return {"error": str(e)}

@sp.post("/create-superadmin/")
async def create_superadmin_user(
    session: SessionDep,
    # tenant: str = Depends(get_tenant), 
       
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
        

        service_provider_scope_group = ScopeGroup(
            scope_name="Super Admin Scope",
        )
        
        session.add(service_provider_scope_group)
        session.commit()
        session.refresh(service_provider_scope_group)

        # Check if System Admin ScopeGroup exists
        system_admin_scope_group = session.exec(
            select(ScopeGroup).where(ScopeGroup.scope_name == "System Admin Scope")
        ).first()
        if not system_admin_scope_group:        
            tenant_scope_group = ScopeGroup(
                scope_name="System Admin Scope",
            )
            session.add(tenant_scope_group)
            session.commit()
            session.refresh(tenant_scope_group)
        
        scope_group_link = ScopeGroupLink(
            scope_group_id=service_provider_scope_group.id,
            organization_id=organization.id,
        )
        
        session.add(scope_group_link)
        session.commit()
        session.refresh(scope_group_link)
        
        super_admin_user = User(
            username=username,
            email=email,
            hashedPassword=get_password_hash(password + username),
            organization_id=organization.id,
            scope_group_id=service_provider_scope_group.id,
        )
        session.add(super_admin_user)
        session.commit()
        session.refresh(super_admin_user)

        return {"message": "Superadmin created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@sp.delete("/delete-superadmin/")
async def delete_superadmin_user(
    session: SessionDep,
    current_user: UserDep,    
    # tenant: str = Depends(get_tenant),

    super_admin_id: int = Body(...),
):
    try:
        superadmin = session.exec(select(User).where(User.id == super_admin_id)).first()
        if not superadmin:
            raise HTTPException(status_code=404, detail="Superadmin not found")

        # Fetch the ScopeGroup associated with the superadmin
        scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == superadmin.scope_group_id)).first()
        if not scope_group:
            raise HTTPException(status_code=404, detail="ScopeGroup not found for the superadmin")

        # Fetch and delete all ScopeGroupLinks associated with the ScopeGroup
        scope_group_links = session.exec(select(ScopeGroupLink).where(ScopeGroupLink.scope_group_id == scope_group.id)).all()
        for link in scope_group_links:
            session.delete(link)
            
        session.delete(superadmin)
        session.commit()

        return {"message": "Superadmin and all related entities deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@sp.get("/tenant-form/")
async def get_tenant_form_fields(
    session: SessionDep,
    # tenant: str, 
    current_user: User = Depends(get_current_user)
):
    try:
        
        tenant_data = {
            "id": "",
            "organization_name": "",
            "owner_name": "",
            "description": "",
            "logo_image": ""
            }
        

        return {"data": tenant_data, "html_types": get_html_types(Organization)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@sp.post("/create-tenant")
async def create_tenant(
    session: SessionDep,
    current_user: UserDep,
    # tenant: str,

    tenant_name: str = Body(...),
    description: str = Body(...),
    logo_image: str = Body(...),
    organization_type: str = Body(...),
):
    try:
        existing_tenant = session.exec(
            select(Organization).where(Organization.organization_name == tenant_name)
        ).first()
        if existing_tenant:
            raise HTTPException(status_code=400, detail="Tenant already exists")

        # if not logo_image or not validate_image(logo_image):
        #     raise HTTPException(status_code=400, detail="Logo image is not valid")

        new_tenant = Organization(
            organization_name=tenant_name,
            description=description,
            logo_image=logo_image,
            organization_type=organization_type,
        )
        session.add(new_tenant)
        session.commit()
        session.refresh(new_tenant)

        # Fetch the System Admin ScopeGroup
        system_admin_scope_group = session.exec(
            select(ScopeGroup).where(ScopeGroup.scope_name == "System Admin Scope")
        ).first()
        if not system_admin_scope_group:
            raise HTTPException(status_code=400, detail="System Admin ScopeGroup not found")

        # Link the System Admin ScopeGroup to the tenant organization
        scope_group_link = ScopeGroupLink(
            scope_group_id=system_admin_scope_group.id,
            organization_id=new_tenant.id,
        )
        session.add(scope_group_link)
        session.commit()

        role_name = f"{tenant_name} System Admin"
        role = Role(
            name=role_name,
            organization_id=new_tenant.id,
        )
        session.add(role)
        session.commit()
        session.refresh(role)

        raw_password = generate_random_password()
        hashed_password = get_password_hash(raw_password + tenant_name)

        tenant_admin = User(
            username=f"{tenant_name.lower()}_admin",
            fullname=f"{tenant_name} Admin",
            email=f"{tenant_name.lower()}_admin@{tenant_name}.com",
            hashedPassword=hashed_password,
            organization=new_tenant.id,
            role_id=role.id,
            scope=Scope.managerial_scope,
            scope_group_id=system_admin_scope_group.id,
        )
        session.add(tenant_admin)
        session.commit()
        session.refresh(tenant_admin)

        return {
            "message": "Tenant and system admin created successfully",
            "tenant": tenant_name,
            "admin_username": tenant_admin.username,
            "admin_password": raw_password 
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    