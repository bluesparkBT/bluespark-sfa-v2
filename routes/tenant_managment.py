import copy
from typing import Annotated, List, Dict, Any
from datetime import timedelta, date, datetime
from fastapi import APIRouter, HTTPException, Body, status, Depends, Path
from models.Warehouse import WarehouseGroup
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

from models.Account import (
    User, ScopeGroup,
    ScopeGroupLink,
    Organization,
    OrganizationType,
    RoleModulePermission,
    Scope,
    Role,
    AccessPolicy,
    ActiveStatus,
    ModuleName as modules,
    WarehouseStoreAdminLink
    )

from models.Address import Address, Geolocation
from models.viewModel.AccountsView import TenantView as TemplateView, UpdateTenantView as UpdateTemplateView


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
    "activate": f"/activate-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}

role_modules = {   
    "get": ["Service Provider", "Tenant Management"],
    "get_form": ["Service Provider", "Tenant Management"],
    "create": ["Service Provider", "Tenant Management"],
    "update": ["Service Provider", "Tenant Management"],
    "activate": "Service Provider",
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
                "domain": f"{Domain}/{tenant.tenant_hashed}",
                "Status": tenant.active                
                }
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
        tenant_address = session.exec(select(Address).where(Address.id == entry.address)).first()
        tenant_location = session.exec(select(Geolocation).where(Geolocation.id == entry.geolocation)).first()
        entry_data = {
            "id": entry.id,
            "name": entry.name,
            "owner_name": entry.owner_name,
            "logo_image": entry.logo_image,
            "description": entry.description,
            "country": tenant_address.country if tenant_address else "",
            "city" : tenant_address.city if tenant_address else "",
            "subcity": tenant_address.sub_city if tenant_address else "",
            "woreda": tenant_address.woreda if tenant_address else "",
            "landmark": entry.landmark,
            "latitude": tenant_location.latitude if tenant_location else "",
            "longitude": tenant_location.longitude if tenant_location else ""
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
        tenant_data = {
            "id": "",
            "name": "",
            "owner_name": "",
            "logo_image": "",
            "description": "",
            "country": "",
            "city": "",
            "sub_city": "",
            "woreda": "",
            "landmark": "",
            "latitude": "",
            "longitude": "",
            }
        
        html_types = copy.deepcopy(get_html_types('tenant'))
        # del html_types['parent_organization']
        # del html_types['parent_id']
        # del html_types['organization_type']
        # del html_types['inheritance_group']

        return {"tabs": {"tenant_info": ["name","owner_name", "description", "logo_image" ],
                         "address": ["country", "city", "sub_city", "woreda", "landmark", "lattitude", "longitude"]},
                "data": tenant_data, "html_types": html_types}
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
                Organization.parent_organization == None
            )
        ).first()
        if existing_entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A Tenant with this name already exists under the same service provider.",
            )
        def parse_float(val):
            if val == "":
                return None
            if isinstance(val, float):
                return val
            try:
                return float(val)
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="Latitude/Longitude must be a float or null.")
        
        org_geolocation = None
        tenant_address = None
        if valid.country is not None and valid.city is not None:
            tenant_address = Address(
                country = valid.country,
                city = valid.city,
                sub_city = valid.sub_city,
                woreda = valid.woreda
            )
            session.add(tenant_address)
            session.commit()
            session.refresh(tenant_address)

        latitude = parse_float(valid.latitude)
        longitude = parse_float(valid.longitude)
        if latitude is not None and longitude is not None:
            org_geolocation = Geolocation(
                name=f"{valid.name} location",
                address_id=tenant_address.id,
                latitude = latitude,
                longitude =  longitude,
            )
            session.add(org_geolocation)
            session.commit()
            session.refresh(org_geolocation)

        hashed_tenant_name = get_tenant_hash(valid.name) 
        tenant = Organization(
            name = valid.name,
            tenant_hashed = hashed_tenant_name,
            owner_name = valid.owner_name,
            description= valid.description,
            logo_image=valid.logo_image,
            organization_type=OrganizationType.company.value,
            tenant_domain = f"{Domain}/{hashed_tenant_name}",
            parent_organization = None,
            landmark = valid.landmark,
            address = tenant_address.id if tenant_address else None,
            geolocation = org_geolocation.id if org_geolocation else None
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
            modules.inventory_management.value
            
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

        
        warehouse_group = WarehouseGroup(
            id = None,
            name = f"{valid.name} Admin Warehouse Group",
            access_policy= AccessPolicy.manage,
            organization_id=tenant.id
        )

        session.add(warehouse_group)
        session.commit()
        session.refresh(warehouse_group)

        link = WarehouseStoreAdminLink(
                id=None,
                user_id = tenant_admin.id,
                warehouse_group_id = warehouse_group.id,
            )
        session.add(link)
        session.commit()
        session.refresh(link)
        
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
    valid: UpdateTemplateView,
):
    try:
        if not check_permission(
            session, "Update", role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        selected_tenant = session.exec(
            select(db_model).where(db_model.id.in_(organization_ids), db_model.id == valid.id)
        ).first()
        print("the selected tenant is ", selected_tenant)
        if not selected_tenant:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

        def parse_float(val):
            if val == "":
                return None
            if isinstance(val, float):
                return val
            try:
                return float(val)
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="Latitude/Longitude must be a float or null.")

        latitude = parse_float(valid.latitude)
        longitude = parse_float(valid.longitude)
        new_tenant_geolocation = None
        new_tenant_address = None
        if valid.country is not None and valid.city is not None:
            exisitng_tenant_address = session.exec(select(Address).where(Address.id == selected_tenant.address)).first()  
            if exisitng_tenant_address:
                if valid.country:
                    exisitng_tenant_address.country = valid.country
                if valid.city:
                    exisitng_tenant_address.city = valid.city,
                if valid.sub_city:
                    exisitng_tenant_address.sub_city = valid.sub_city,
                if valid.woreda:
                    exisitng_tenant_address.woreda = valid.woreda
            else:
                new_tenant_address = Address(
                    country = valid.country,
                    city = valid.city,
                    sub_city = valid.sub_city,
                    woreda = valid.woreda
                )
                session.add(new_tenant_address)
                session.commit()
                session.refresh(new_tenant_address)
            
        if latitude is not None and longitude is not None:  
            exisitng_tenant_geolocation = session.exec(select(Geolocation).where(Geolocation.id == selected_tenant.geolocation)).first()  
            if exisitng_tenant_geolocation:
                if valid.latitude:
                    exisitng_tenant_geolocation.latitude = latitude,
                if valid.longitude:
                    exisitng_tenant_geolocation.longitude = longitude
                    
                session.add(exisitng_tenant_geolocation)
                session.commit()            
            else:
                new_tenant_geolocation = Geolocation(
                    name = f"{valid.name} location",
                    latitude = latitude,
                    longitude = longitude,
                    address = new_tenant_address.id if new_tenant_address else exisitng_tenant_address.id,

                )
                session.add(new_tenant_geolocation)
                session.commit()
                session.refresh(new_tenant_geolocation)
                selected_tenant.geolocation = new_tenant_geolocation.id

        selected_tenant.name = valid.name
        selected_tenant.owner_name = valid.owner_name
        selected_tenant.description= valid.description
        selected_tenant.logo_image=valid.logo_image
        # selected_tenant.organization_type=OrganizationType.company.value
        # selected_tenant.parent_organization = None
        selected_tenant.address = new_tenant_address.id if new_tenant_address else exisitng_tenant_address.id
        selected_tenant.geolocation = new_tenant_geolocation.id if new_tenant_geolocation else exisitng_tenant_geolocation.id
        if valid.landmark:
            selected_tenant.landmark = valid.landmark
    
        session.add(selected_tenant)
        session.commit()
        session.refresh(selected_tenant)
        return {"message": f"{endpoint_name} Updated successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

# @tr.put(endpoint['archive']+ "/{id}")
# def archive_template(
#     session: SessionDep, 
#     current_user: UserDep,
#     id: int
# ) :
#     """
#     Soft delete/ archive (inactive) a tenant organization and all its related records.
#     """
#     try:
#         if not check_permission(
#             session, "Update", role_modules['archive'], current_user
#             ):
#             raise HTTPException(
#                 status_code=403, detail="You Do not have the required privilege"
#             )
#         organization_ids = get_organization_ids_by_scope_group(session, current_user)
#         selected_entry = session.exec(
#             select(db_model).where(db_model.id.in_(organization_ids), db_model.id == id)
#         ).first()
#         print("tennat is found and have the status of:::::::", selected_entry.active)

#         if not selected_entry:
#             raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")
        
#         if selected_entry.active == "active":
#             selected_entry.active = ActiveStatus.inactive
#             session.commit()

#         return {"message": f"{endpoint_name} archived successfully"}
#     except HTTPException as http_exc:
#         raise http_exc
#     except Exception:
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail="Something went wrong")

@tr.put(endpoint['activate']+ "/{id}")
def active_template(
    session: SessionDep, 
    current_user: UserDep,
    id: int
) :
    """
    Active/ inactive a tenant organization and all its related records.
    """
    try:
        if not check_permission(
            session, "Update", role_modules['activate'], current_user
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
        if selected_entry.active == "active":
            selected_entry.active = ActiveStatus.inactive
            session.commit()
            session.refresh(selected_entry)
            print("Tenant has been Deactivated")
        else:
            selected_entry.active = ActiveStatus.active
            session.commit()
            session.refresh(selected_entry)
            print("Tenant has been Activated")

    
        return {"message": f"{endpoint_name} Status changed successfully"}
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
