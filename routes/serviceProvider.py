
from typing import Annotated, List, Dict, Any
from datetime import timedelta, date, datetime
from fastapi import APIRouter, HTTPException, Body, status, Depends, Path
from sqlmodel import select, Session
from db import get_session
from models.Account import User, ScopeGroup, ScopeGroupLink, Organization, OrganizationType, RoleModulePermission, Scope, Role, AccessPolicy
from models.Account import ModuleName as modules
from utils.auth_util import verify_password, create_access_token, get_password_hash
from utils.util_functions import validate_name, validate_email, validate_phone_number, parse_enum
from utils.auth_util import get_current_user, check_permission, generate_random_password, get_tenant_hash, extract_username, add_organization_path
from utils.model_converter_util import get_html_types
from utils.get_hierarchy import get_child_organization
from utils.domain_util import getPath
import traceback

# frontend domain
Domain= getPath()

#for dev environment localhost
# Domain= "http://127.0.0.1:3000"

service_provider_company = "Bluespark"
ACCESS_TOKEN_EXPIRE_DAYS = 2

ServiceProvider =sp= APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

@sp.get("/has-superadmin")
def has_superadmin_created(
    session: SessionDep
) ->bool:
    existing_superadmin = session.exec(select(User).where(User.role_id == Role.id == "Super Admin")).first()
    if existing_superadmin:
        print("Super admin and tenant already exisits")
        return True
    else: 
        return False
    

@sp.post("/login/")
def login(
    session: SessionDep,
    
    username: str = Body(...),
    password: str = Body(...)
):
    try:
        service_provider = session.exec(select(Organization).where(Organization.organization_type == "Service Provider")).first()
        db_username = add_organization_path(username, service_provider.organization_name)

        user = session.exec(select(User).where(User.username == db_username)).first()
        if not user or not verify_password(password+db_username, user.hashedPassword):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
        access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
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
        traceback.print_exc()
        return {"error": str(e)}

@sp.post("/create-superadmin/")
async def create_superadmin_user(
    session: SessionDep,
    fullname: str = Body(...),
    username: str = Body(...),
    email: str = Body(...),
    password: str = Body(...),
):
    try:
        existing_superadmin = session.exec(select(User).where(User.role_id == Role.id == "Super Admin")).first()
        if existing_superadmin is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Superadmin already registered",
            )

        service_provider = Organization(
            organization_name= "Blue Spark Business Technology",
            owner_name = "Mekonen",
            organization_type = OrganizationType.service_provider.value
        )

        session.add(service_provider)
        session.commit()
        session.refresh(service_provider)
        
        # Check if Super Admin Scope group exists
        existing_scope_group = session.exec(
            select(ScopeGroup).where(ScopeGroup.scope_name == "Super Admin Scope")
        ).first()

        if existing_scope_group:
            service_provider_scope_group = existing_scope_group
        else:
            service_provider_scope_group = ScopeGroup(
                scope_name="Super Admin Scope",
                parent_id = service_provider.id
                )
            session.add(service_provider_scope_group)
            session.commit()
            session.refresh(service_provider_scope_group)

        
        scope_group_link = ScopeGroupLink(
            scope_group_id=service_provider_scope_group.id,
            organization_id=service_provider.id,
        )
        
        session.add(scope_group_link)
        session.commit()
        session.refresh(scope_group_link)
        
        #create role
        role = Role(
            name="Super Admin",
            organization_id = service_provider.id
        )
        session.add(role)
        session.commit()
        session.refresh(role)

        # List of modules the Super Admin should have access to
        modules_to_grant = [
            modules.service_provider.value,
            modules.role.value,
            modules.administrative.value,
            modules.scope_group.value,
            modules.users.value
        ]
        for module in modules_to_grant: 
            role_module_permission= RoleModulePermission(
                role_id=role.id,
                module=module,
                access_policy=AccessPolicy.manage
            )
            session.add(role_module_permission)
        session.commit()
        
        stored_username = add_organization_path(username, service_provider.organization_name)
        super_admin_user = User(
            fullname = fullname,
            username= stored_username,
            email=email,
            hashedPassword=get_password_hash(password + stored_username),
            organization_id=service_provider.id,
            scope_group_id=service_provider_scope_group.id,
            role_id = role.id,
            scope = Scope.managerial_scope.value
        )
        session.add(super_admin_user)
        session.commit()
        session.refresh(super_admin_user)

        return {"message": "Superadmin created successfully"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@sp.delete("/delete-superadmin/")
async def delete_superadmin_user(
    session: SessionDep,
    current_user: UserDep,    

    super_admin_id: int = Body(...),
):
    try:
        if not check_permission(session, "Delete", "Service Provider", current_user):
            raise HTTPException(
                status_code=403, detail="You do not have the required privilege"
            )
        superadmin = session.exec(select(User).where(User.id == super_admin_id)).first()
        if not superadmin:
            raise HTTPException(status_code=404, detail="Superadmin not found")

        # Fetch the ScopeGroup associated with the superadmin
        scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == superadmin.scope_group_id)).first()
        if not scope_group:
            raise HTTPException(status_code=404, detail="ScopeGroup not found for the superadmin")

        # cascade delete all attributes linked to superadmin.
        scope_group_links = session.exec(select(ScopeGroupLink).where(ScopeGroupLink.scope_group_id == scope_group.id)).all()
        for link in scope_group_links:
            session.delete(link)
        
        session.delete(scope_group)
            
        session.delete(superadmin)
        session.commit()

        return {"message": "Superadmin and all related entities deleted successfully"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@sp.get("/get-service-provider/")
async def get_service_provider(
    session: SessionDep,
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
            session, "Read", "Service Provider", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        # Query the organization associated with the logged-in user
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

@sp.get("/{tenant}/get-my-tenant/")
async def get_my_tenant(
    session: SessionDep,
    tenant: str,    
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
        organization = session.exec(select(Organization).where(Organization.tenant_hashed == tenant)).first()
        print("the current tenant is ",organization)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="tenant not found for the logged-in user",
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

@sp.get("/get-tenants")
async def get_tenants(
    session: SessionDep,
    current_user: UserDep,
):
    """
    Retrieve all tenant companies that use the system.
    """
    try:
        if not check_permission(session, "Read", "Service Provider", current_user):
            raise HTTPException(
                status_code=403, detail="You do not have the required privilege"
            )
        tenant_list = []
        
        tenants = session.exec(
            select(Organization).where(
                (Organization.organization_type == OrganizationType.company)
            )).all()
        # tenants = get_child_organization(session, None, 1 )
        # print(tenants)
        for tenant in  tenants:
            tenant_list.append({
                    "id": tenant.id,
                    "tenant": tenant.organization_name,
                    "owner": tenant.owner_name,
                    "description": tenant.description,
                    "logo": tenant.logo_image,
                    "domain": f"{Domain}/{tenant.tenant_hashed}"                }
            )

        return tenant_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@sp.get("/get-tenant/{id}")
async def get_tenant(
    session: SessionDep,
    current_user: UserDep,
    id: int
):
    """
    Retrieve all tenant companies that use the system.
    """
    try:
        if not check_permission(session, "Read", "Service Provider", current_user):
            raise HTTPException(
                status_code=403, detail="You do not have the required privilege"
            )

        tenant = session.exec(
            select(Organization).where(
                (Organization.id == id)) ).first()
     

        tenant_data = {
                "id": tenant.id,
                "tenant_name": tenant.organization_name,
                "owner_name": tenant.owner_name,
                "description": tenant.description,
                "logo_image": tenant.logo_image,
                "organization_type": tenant.organization_type,
                "domain": f"{Domain}/{tenant.tenant_hashed}"

                
            }
       

        return tenant_data

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@sp.get("/tenant-form/")
async def get_tenant_form_fields(
    session: SessionDep,
    current_user: UserDep
):
    try:
        if not check_permission(session, "Read", "Service Provider", current_user):
            raise HTTPException(
                status_code=403, detail="You do not have the required privilege"
            )
        tenant_data = {
            "id": "",
            "tenant_name": "",
            "owner_name": "",
            "description": "",
            "logo_image": "",
            # "organization_type" : {i.value: i.value for i in OrganizationType},
            
            }
        

        return {"data": tenant_data, "html_types": get_html_types('organization')}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@sp.post("/create-tenant")
async def create_tenant(
    session: SessionDep,
    current_user: UserDep,

    tenant_name: str = Body(...),
    owner_name: str = Body(...),
    description: str = Body(...),
    logo_image: str = Body(...),

):
    try:
        if not check_permission(session, "Create", "Service Provider", current_user):
            raise HTTPException(
                status_code=403, detail="You do not have the required privilege"
            )
            
        # existing_tenant = session.exec(
        #     select(Organization).where(Organization.organization_name == verify_tenant(tenant_name))
        # ).first()

        print("current user of provide is:", current_user)
        superadmin_id = session.exec(select(User.organization_id).where(User.role_id == Role.id == "Super Admin")).first()
        
        hashed_tenant_name = get_tenant_hash(tenant_name) 
        tenant = Organization(
            organization_name = tenant_name,
            tenant_hashed = hashed_tenant_name,
            owner_name = owner_name,
            description=description,
            logo_image=logo_image,
            organization_type=OrganizationType.company.value,
            tenant_domain = f"{Domain}/{hashed_tenant_name}",
            parent_id = superadmin_id
        )
        session.add(tenant)
        session.commit()
        session.refresh(tenant)

        # Fetch the System Admin ScopeGroup
        system_admin_scope_group = session.exec(
            select(ScopeGroup).where(ScopeGroup.scope_name == f"{tenant_name} Admin Scope")
        ).first()

        if not system_admin_scope_group:
            system_admin_scope_group = ScopeGroup(
                scope_name=f"{tenant_name} Admin Scope",
                parent_id = tenant.id
            )
            session.add(system_admin_scope_group)
            session.commit()
            session.refresh(system_admin_scope_group)
            

        # Link the System Admin ScopeGroup to the tenant organization
        scope_group_link = ScopeGroupLink(
            scope_group_id=system_admin_scope_group.id,
            organization_id=tenant.id,
        )
        session.add(scope_group_link)
        session.commit()
        
        super_admin_scope_group = session.exec(
            select(ScopeGroup).where(ScopeGroup.scope_name == "Super Admin Scope")
        ).first()

        existing_link = session.exec(
            select(ScopeGroupLink).where(
                ScopeGroupLink.scope_group_id == super_admin_scope_group.id,
                ScopeGroupLink.organization_id == tenant.id
            )
        ).first()
        print("exisintg link", existing_link)
        if not existing_link:
            super_admin_scope_link = ScopeGroupLink(
                scope_group_id=super_admin_scope_group.id,
                organization_id= tenant.id
            )
            session.add(super_admin_scope_link)
            session.commit()
            print("superadmin link updated", super_admin_scope_group)
            
            
        role = Role(
            name=f"{tenant_name} System Admin",
            organization_id=tenant.id,
        )
        session.add(role)
        session.commit()
        session.refresh(role)
        
        
        # List of modules the tenant system Admin should have access to
        modules_to_grant = [
            modules.administrative.value,
            modules.role.value,
            modules.scope_group.value,
            modules.users.value,
            modules.inheritance.value,
            modules.category.value,
            modules.product.value,
            modules.warehouse.value,
            modules.sales.value,
            modules.organization.value,
            modules.territory.value,
            modules.route.value,
            modules.address.value,
            
            
        ]
        for module in modules_to_grant: 
            role_module_permission= RoleModulePermission(
                role_id=role.id,
                module=module,
                access_policy=AccessPolicy.manage
            )
            session.add(role_module_permission)
        session.commit()
        
        password = generate_random_password()
        hashed_password = get_password_hash(password + add_organization_path("admin", tenant_name))

        tenant_admin = User(
            username= add_organization_path("admin", tenant_name),
            fullname= "System Admin",
            email=f"{tenant_name.lower()}_admin@{tenant_name}.com",
            hashedPassword = hashed_password,
            organization_id=tenant.id,
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
            "domain": f"{Domain}/{hashed_tenant_name}/signin/",
            "username":"admin",
            "password": password 
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@sp.put("/update-tenant")
async def update_tenant(
    session: SessionDep,
    current_user: UserDep,
    id: int = Body(...),
    tenant_name: str = Body(...),
    owner_name: str = Body(...),
    description: str = Body(...),
    logo_image: str = Body(...),
):
    try:
        if not check_permission(session, "Update", "Service Provider", current_user):
            raise HTTPException(
                status_code=403, detail="You do not have the required privilege"
            )

        existing_tenant = session.exec(
            select(Organization).where(Organization.id == id)
        ).first()

        if not existing_tenant:
            raise HTTPException(status_code=400, detail="Tenant does not exist")

        # Check for conflicting tenant name (optional)
        if tenant_name != existing_tenant.organization_name:
            name_conflict = session.exec(
                select(Organization).where(Organization.organization_name == tenant_name)
            ).first()
            if name_conflict:
                raise HTTPException(status_code=400, detail="Tenant name already exists")

        # Update tenant fields
        hashed_tenant_name = get_tenant_hash(tenant_name)
        existing_tenant.organization_name = tenant_name
        existing_tenant.owner_name = owner_name
        existing_tenant.description = description
        existing_tenant.logo_image = logo_image
        existing_tenant.tenant_hashed = hashed_tenant_name

        session.add(existing_tenant)
        session.commit()
        session.refresh(existing_tenant)

        # Update ScopeGroup name (if exists)
        scope_group_link = session.exec(
            select(ScopeGroupLink).where(ScopeGroupLink.organization_id == existing_tenant.id)
        ).first()

        if scope_group_link:
            scope_group = session.get(ScopeGroup, scope_group_link.scope_group_id)
            if scope_group:
                scope_group.scope_name = f"{tenant_name} Admin Scope"
                session.add(scope_group)
                session.commit()

        # Update Role name (if exists)
        role = session.exec(
            select(Role).where(Role.organization_id == existing_tenant.id)
        ).first()
        if role:
            role.name = f"{tenant_name} System Admin"
            session.add(role)
            session.commit()

        updated_data = {
            "tenant_name": existing_tenant.organization_name,
            "tenant_owner": existing_tenant.owner_name,
            "domain": f"{Domain}/{existing_tenant.tenant_hashed}",
        }

        return {"message": "Tenant updated successfully", "tenant": updated_data}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


# @sp.delete("/archive-tenant/{id}")
# async def archive_tenant(
#     session: SessionDep,
#     current_user: UserDep,
#     tenant: str,
#     id: int
# ):
#     """
#     Soft delete (archive) a tenant organization and all its related records.
#     """
#     try:
#         if not check_permission(session, "Delete", "Service Provider", current_user):
#             raise HTTPException(
#                 status_code=403, detail="You do not have the required privilege"
#             )

#         # Fetch the tenant/organization
#         tenant = session.get(Organization, id)
#         if not tenant:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Organization not found",
#             )

#         # Soft-delete the organization
#         tenant.active = False

#         # Soft-delete all related child organizations
#         child_orgs = session.exec(
#             select(Organization).where(Organization.parent_id == tenant.id)
#         ).all()
#         for child in child_orgs:
#             child.active = False

#         # Soft-delete all users
#         users = session.exec(
#             select(User).where(User.organization_id == tenant.id)
#         ).all()
#         for user in users:
#             user.active = False

#         # Soft-delete roles
#         roles = session.exec(
#             select(Role).where(Role.organization_id == tenant.id)
#         ).all()
#         for role in roles:
#             role.active = False

#         # Soft-delete products (if applicable)
#         products = session.exec(
#             select(Product).where(Product.organization_id == tenant.id)
#         ).all()
#         for product in products:
#             product.active = False

#         # Soft-delete warehouses (if applicable)
#         warehouses = session.exec(
#             select(Warehouse).where(Warehouse.organization_id == tenant.id)
#         ).all()
#         for wh in warehouses:
#             wh.active = False

#         session.commit()
#         return {"message": "Tenant organization archived successfully"}

#     except Exception as e:
#         traceback.print_exc()
#         raise HTTPException(status_code=400, detail=str(e))
