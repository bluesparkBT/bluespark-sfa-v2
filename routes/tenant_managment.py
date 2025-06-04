import copy
from typing import Annotated, List, Dict, Any
from datetime import timedelta, date, datetime
from fastapi import APIRouter, HTTPException, Body, status, Depends, Path
from sqlmodel import select, Session
from db import get_session
import traceback
from utils.auth_util import verify_password, create_access_token, get_password_hash
from utils.util_functions import validate_name, validate_email, validate_phone_number, parse_enum
from utils.auth_util import get_current_user, check_permission, generate_random_password, get_tenant_hash, extract_username, add_organization_path
from utils.model_converter_util import get_html_types
from utils.form_db_fetch import get_organization_ids_by_scope_group, fetch_organization_id_and_name, fetch_inheritance_group_id_and_name, fetch_address_id_and_name
from utils.domain_util import getPath
from utils.auth_util import check_permission_and_scope

from models.Account import User, ScopeGroup, ScopeGroupLink, Organization, OrganizationType, RoleModulePermission, Scope, Role, AccessPolicy
from models.Account import ModuleName as modules
from models.viewModel.AccountsView import TenantView as TemplateView

# frontend domain
Domain= getPath()

TenantRouter = tr = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]
 
endpoint_name = "tenant"
db_model = Organization

endpoint = {
    "get": f"/get-{endpoint_name}s",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",
    "update": f"/update-{endpoint_name}",
    "archive": f"/archive-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}

role_modules = {   
    "get": ["Service Provider", "Tenant Management"],
    "get_form": ["Service Provider", "Tenant Management"],
    "create": ["Service Provider", "Tenant Management"],
    "update": ["Service Provider", "Tenant Management"],
    "archive": "Service Provider",
    "delete": "Service Provider",
}

@tr.get("/{tenant}/get-my-tenant/")
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
        organization = session.exec(select(db_model).where(db_model.tenant_hashed == tenant)).first()
        print("the current tenant is ",organization)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="tenant not found for the logged-in user",
            )

        # Return the organization information
        return {
            "id": organization.id,
            "organization": organization.name,
            "owner": organization.owner_name,
            "logo": organization.logo_image,
        }
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

#CRUD
@tr.get(endpoint['get'])
def get(
    session: SessionDep,
    current_user: UserDep,
):
    try:
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        entries_list = session.exec(
            select(db_model).where(db_model.id.in_(organization_ids), db_model.organization_type == "Company")
        ).all()
        
        if not entries_list or entries_list is None:
            raise HTTPException(status_code=400, detail="No Tenants Created")
        tenant_list = []

        for tenant in  entries_list:
            tenant_list.append({
                "id": tenant.id,
                "tenant": tenant.name,
                "owner": tenant.owner_name,
                "description": tenant.description,
                "logo": tenant.logo_image,
                "domain": f"{Domain}/{tenant.tenant_hashed}"                }
            )

        return tenant_list

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

@tr.get(endpoint['get_by_id'] + "/{id}")
def get_by_Id_template(
    session: SessionDep, 
    current_user: UserDep,
    id: int,
):
    try:
        if not check_permission(
            session, "Create",role_modules['get_form'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            ) 
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        entry = session.exec(
            select(db_model).where(db_model.id.in_(organization_ids), db_model.id == id)
        ).first()

        if not entry:
            raise HTTPException(status_code=404, detail= f"{endpoint_name} not found")
            
        entry_data = {
            "id": entry.id,
            "name": entry.name,
            "owner_name": entry.owner_name,
            "description": entry.description,
            "logo_image": entry.logo_image,
            "organization_type": entry.organization_type,
            "inheritance_group": entry.inheritance_group,
            "address": entry.address,
            "landmark": entry.landmark,
            "latitude": entry.geolocation.latitude,
            "longitude": entry.geolocation.longitude,
            }
        
        return entry_data
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")


@tr.get("/tenant-form/")
async def get_tenant_form_fields(
    session: SessionDep,
    current_user: UserDep
):
    try:
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        parent_org =  session.exec(select(Organization.id))
        tenant_data = {
            "id": "",
            "name": "",
            "owner_name": "",
            "description": "",
            "logo_image": "",
            "organization_type": {i.value: i.value for i in OrganizationType},
            "inheritance_group": fetch_inheritance_group_id_and_name(session,current_user),
            "address": fetch_address_id_and_name(session,current_user),
            "landmark": "",
            "latitude": "",
            "longitude": "",
            }
        
        html_types = copy.deepcopy(get_html_types('organization'))
        del html_types['parent_organization']
        del html_types['parent_id']
        del html_types['geolocation']
        return {"data": tenant_data, "html_types": html_types}
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")  


@tr.post(endpoint['create'])
def create_template(
    session: SessionDep,
    current_user: UserDep,
    valid: TemplateView,
):
    try:
        if not check_permission(
            session, "Create", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        service_provider = session.exec(select(User.organization).where(User.role == Role.id == "Super Admin")).first()
        existing_entry = session.exec(
            select(Organization).where(
                Organization.name == valid.name,
                Organization.parent_organization == valid.parent_organization
            )
        ).first()
        if existing_entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A Tenant with this name already exists under the same service provider.",
            )
        hashed_tenant_name = get_tenant_hash(valid.name) 
        tenant = Organization(
            name = valid.name,
            tenant_hashed = hashed_tenant_name,
            owner_name = valid.owner_name,
            description= valid.description,
            logo_image=valid.logo_image,
            organization_type=OrganizationType.company.value,
            tenant_domain = f"{Domain}/{hashed_tenant_name}",
            parent_organization = service_provider
        )
        session.add(tenant)
        session.commit()
        session.refresh(tenant)

        # Fetch the System Admin ScopeGroup
        system_admin_scope_group = session.exec(
            select(ScopeGroup).where(ScopeGroup.name == f"{valid.name} Admin Scope")
        ).first()

        if not system_admin_scope_group:
            system_admin_scope_group = ScopeGroup(
                name=f"{valid.name} Admin Scope",
                tenant_id = tenant.id
            )
            session.add(system_admin_scope_group)
            session.commit()
            session.refresh(system_admin_scope_group)
            
        # Link the System Admin ScopeGroup to the tenant organization
        scope_group_link = ScopeGroupLink(
            scope_group=system_admin_scope_group.id,
            organization=tenant.id,
        )
        session.add(scope_group_link)
        session.commit()
        
        super_admin_scope_group = session.exec(
            select(ScopeGroup).where(ScopeGroup.name == "Super Admin Scope")
        ).first()

        existing_link = session.exec(
            select(ScopeGroupLink).where(
                ScopeGroupLink.scope_group == super_admin_scope_group.id,
                ScopeGroupLink.organization == tenant.id
            )
        ).first()
        if not existing_link:
            super_admin_scope_link = ScopeGroupLink(
                scope_group=super_admin_scope_group.id,
                organization= tenant.id
            )
            session.add(super_admin_scope_link)
            session.commit()
            print("superadmin link updated", super_admin_scope_group)
            
        role = Role(
            name=f"{valid.name} System Admin",
            organization=tenant.id,
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
                role=role.id,
                module=module,
                access_policy=AccessPolicy.manage
            )
            session.add(role_module_permission)
        session.commit()
        
        password = generate_random_password()
        hashed_password = get_password_hash(password + add_organization_path("admin", valid.name))

        tenant_admin = User(
            username= add_organization_path("admin", valid.name),
            full_name= "System Admin",
            email=f"{valid.name.lower()}_admin@{valid.name}.com",
            hashedPassword = hashed_password,
            organization=tenant.id,
            role=role.id,
            scope=Scope.managerial_scope,
            scope_group=system_admin_scope_group.id,
        )
        session.add(tenant_admin)
        session.commit()
        session.refresh(tenant_admin)
        
        return {
            "message": "Tenant and system admin created successfully",
            "tenant": valid.name,
            "domain": f"{Domain}/{hashed_tenant_name}/signin/",
            "username":"admin",
            "password": password 
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
 
@tr.put(endpoint['update'])
def update_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    valid: TemplateView,
):
    try:
        if not check_permission(
            session, "Update", role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        selected_entry = session.exec(
            select(db_model).where(db_model.id.in_(organization_ids), db_model.id == valid.id)
        ).first()
        print("fetched selected entry", selected_entry)
        if not selected_entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")
        
        selected_org = session.exec(select(Organization).where(Organization.id == selected_entry.id)).first() 

        selected_org.name = valid.name
        selected_org.owner_name = valid.owner_name
        selected_org.description= valid.description
        selected_org.logo_image=valid.logo_image
        selected_org.organization_type=OrganizationType.company.value
        selected_org.parent_organization = valid.parent_organization
        # selected_org.address = valid.address
    
        session.add(selected_org)
        session.commit()
        session.refresh(selected_org)
        return {"message": f"{endpoint_name} Updated successfully"}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

@tr.put(endpoint['archive']+ "/{id}")
def archive_template(
    session: SessionDep, 
    current_user: UserDep,
    id: int
) :
    """
    Soft delete/ archive (inactive) a tenant organization and all its related records.
    """
    try:
        if not check_permission(
            session, "Update", role_modules['archive'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        selected_entry = session.exec(
            select(db_model).where(db_model.id.in_(organization_ids), db_model.id == id)
        ).first()

        if not selected_entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")
        
        selected_entry.active = False
        session.commit()

        return {"message": f"{endpoint_name} archived successfully"}
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    
@tr.delete(endpoint['delete']+ "/{id}")
async def delete_tenant(
    session: SessionDep,
    current_user: UserDep,
    id: int
):
    try:
        if not check_permission(
            session, "Delete", role_modules['delete'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        # Fetch the tenant/organization
        tenant = session.get(Organization, id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        # Soft-delete the organization
        tenant.active = False
        session.delete(tenant)
        session.commit()
        return {"message": "Tenant and all related data deleted successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
