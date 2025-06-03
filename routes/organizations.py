from operator import or_
from typing import Annotated, List, Dict, Any, Optional, Union
from fastapi import APIRouter, HTTPException, Body, status, Depends, Path
from sqlmodel import select, Session
from db import get_session
from models.Account import User, Organization, OrganizationType, ScopeGroup, Scope, Role, ScopeGroupLink
from models.Address import Address, Geolocation
from utils.auth_util import get_current_user, check_permission
from utils.model_converter_util import get_html_types
from utils.util_functions import validate_name, validate_image
from models.viewModel.AccountsView import OrganizationView as TemplateView, UpdateOrganizationView as UpdateTemplateView 
from utils.get_hierarchy import get_organization_ids_by_scope_group, get_child_organization, get_heirarchy
from utils.form_db_fetch import fetch_organization_id_and_name, fetch_inheritance_group_id_and_name, fetch_address_id_and_name, fetch_geolocation_id_and_name
import traceback

OrganizationRouter =tr= APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "organization"
db_model = Organization

endpoint = {
    "get": f"/get-{endpoint_name}s",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",
    "update": f"/update-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}

role_modules = {   
    "get": ["Administrative"],
    "get_form": ["Administrative"],
    "create": ["Administrative"],
    "update": ["Administrative"],
    "delete": ["Administrative"],
}

@tr.get("/get-my-tenant/")
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
            "organization": organization.name,
            "owner": organization.owner_name,
            "logo": organization.logo_image,
        }
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

 
@tr.get("/get-children-organizations/{id}")
async def get_children_organizations(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str,
    id: int
):
    """
    Retrieve children organizations of the given organization id.
    """
    try:
        if not check_permission(
            session, "Read", "Organization", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        
        organizations = session.exec(select(Organization).where(Organization.parent_organization == id)).all()

        if not organizations:
            return []

        organization_list = []

        for org in organizations:
            organization_list.append({
                "id": org.id,
                "organization": org.name,
                "owner": org.owner_name,
                "description": org.description,         
                "logo": org.logo_image,
                "parent_organization": org.parent_organization,
                "organization_type": org.organization_type,
                "inheritance_group": org.inheritance_group,
                "scope_groups": [
                    {"id": sg.id, "name": sg.name}
                    for sg in org.scope_groups
                ]
            })

        return organization_list

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    
@tr.get("/get-my-organization/")
async def get_my_organization(
    session: SessionDep,
    tenant: str,
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
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        organization = session.exec(select(Organization).where(Organization.id == current_user.organization)).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="organization not found for the logged-in user",
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
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    
@tr.get(endpoint['get'])
def get_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    """
    Retrieve all organizations with their associated scope groups.
    """
    try:
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        if tenant == "provider":
            current_tenant = session.exec(select(db_model).where(db_model.id == current_user.organization)).first()
        else :
            current_tenant = session.exec(select(db_model).where(db_model.tenant_hashed == tenant)).first()
        
        organizations = get_heirarchy(session, current_tenant.id, None, current_user)
        if not organizations:
            raise HTTPException(status_code=404, detail="No organizations found")

        return organizations
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
       
@tr.get(endpoint['get_by_id'] + "/{id}")
def get_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int,
):
    try:
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        organization = session.exec(select(db_model).where(db_model.id == id)).first()
        if not organization:
            raise HTTPException(status_code=404, detail= f"{endpoint_name} not found")
  
        return {
            "id": organization.id,
            "name": organization.name,
            "owner_name": organization.owner_name,
            "description": organization.description,
            "logo_image": organization.logo_image,
            "parent_organization": organization.parent_organization,
            "organization_type": organization.organization_type,
            "inheritance_group": organization.inheritance_group,
            "address": organization.address,
            "landmark": organization.landmark,
            "geolocation":organization.geolocation

        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
     
@tr.get(endpoint['get_form'])
def get_template_form(
    tenant: str,
    session: SessionDep,
    current_user: UserDep,
) :
    """   Retrieves the form structure for creating a new user account.
    """
    try:
        # Check permission
        if not check_permission(
            session, "Create",role_modules['get_form'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        organization_data = {
            "id": "",
            "name": "",
            "owner_name": "",
            "description": "",
            "logo_image": "",
            "parent_organization": fetch_organization_id_and_name(session, current_user),
            "organization_type" : {i.value: i.value for i in OrganizationType if i.value !="Service Provider"},
            "inheritance_group": fetch_inheritance_group_id_and_name(session, current_user),
            "address" : fetch_address_id_and_name(session, current_user),
            "landmark" : "",
            "geolocation": fetch_geolocation_id_and_name(session, current_user),
            "latitude" : "",
            "longitude" : "",
            }
        
        return {"data": organization_data, "html_types": get_html_types('organization')}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

@tr.post(endpoint['create'])
def create_template(
    session: SessionDep,
    tenant: str,
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
        existing_entry = session.exec(
            select(db_model).where(
            (db_model.name == valid.name) & (db_model.parent_organization == valid.parent_organization)
            )
        ).first()
        if existing_entry is not None:
            raise HTTPException(
                status_code=404,
                detail= f"{endpoint_name} already registered",
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
        latitude = parse_float(valid.latitude)
        longitude = parse_float(valid.longitude)
        if latitude is not None and longitude is not None:
            org_geolocation = Geolocation(
                name=f"{valid.name} location",
                address_id=valid.address,
                latitude = latitude,
                longitude =  longitude,
            )
            session.add(org_geolocation)
            session.commit()
            session.refresh(org_geolocation)

        organization = Organization(
            id = None,
            name = valid.name,
            owner_name = valid.owner_name,
            description = valid.description,
            logo_image = valid.logo_image,
            parent_organization = valid.parent_organization,
            organization_type = valid.organization_type,
            inheritance_group = valid.inheritance_group,
            address = valid.address,
            landmark= valid.landmark,
            geolocation=org_geolocation.id if org_geolocation else None

        )
        
        session.add(organization)
        session.commit()
        session.refresh(organization)

        scope_group_link = ScopeGroupLink(
            scope_group=current_user.scope_group,
            organization=organization.id,
        )
        session.add(scope_group_link)
        session.commit()
        
        return {"message": "Organization created successfully"}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")           

@tr.put(endpoint['update'])
def update_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    valid: UpdateTemplateView,
):

    try:
        if not check_permission(
            session, "Update",role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        existing_organization = session.exec(select(Organization).where(Organization.id == valid.id)).first()
        if existing_organization is None:
            raise HTTPException(
                status_code=404,
                detail="Organization not found",
        )     
        # def parse_float(val):
        #     if val == "":
        #         return None
        #     if isinstance(val, float):
        #         return val
        #     try:
        #         return float(val)
        #     except (TypeError, ValueError):
        #         raise HTTPException(status_code=400, detail="Latitude/Longitude must be a float or null.")

        # exisitng_org_geolocation = session.exec(select(Geolocation).where(Geolocation.id == existing_organization.address)).first()  
        # latitude = parse_float(valid.latitude)
        # longitude = parse_float(valid.longitude)
        # if latitude is not None and longitude is not None:  
        #     if exisitng_org_geolocation:
        #         if valid.latitude:
        #             exisitng_org_geolocation.latitude = latitude,
        #         if valid.longitude:
        #             exisitng_org_geolocation.longitude = longitude
                    
        #         session.add(exisitng_org_geolocation)
        #         session.commit()            
        #     else:
        #         org_geolocation = Geolocation(
        #             name = f"{valid.name} location",
        #             address = valid.address,
        #             latitude = latitude,
        #             longitude = longitude
        #         )
        #         session.add(org_geolocation)
        #         session.commit()

        
        existing_organization.name = valid.name
        existing_organization.owner_name = valid.owner_name
        existing_organization.description = valid.description
        if valid.inheritance_group:
            existing_organization.inheritance_group= valid.inheritance_group
        existing_organization.logo_image = valid.logo_image
        existing_organization.organization_type = valid.organization_type
        if valid.parent_organization:
            existing_organization.parent_organization = valid.parent_organization
        if valid.address:
            existing_organization.address = valid.address
        if valid.landmark:
            existing_organization.landmark = valid.landmark,
        if valid.geolocation:
            existing_organization.geolocation = valid.geolocation
            
        session.add(existing_organization)
        session.commit()
        session.refresh(existing_organization)
        
        return {"message": f"{endpoint_name} updated successfully"}
    
    except Exception as e:
        traceback.print_exc()
        
        raise HTTPException(status_code=400, detail=str(e)) 

@tr.delete("/delete-organization/{id}")
async def delete_organization(
    session: SessionDep,
    current_user: UserDep,
    id: int,    
    tenant: str,
):
    """
    Delete an organization by ID.

    Args:
        session (SessionDep): Database session.
        id (int): ID of the organization to delete.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException: 404 if the organization is not found.
    """
    try:
        if not check_permission(
            session, "Delete", "Organization", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        organization = session.get(Organization, id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        # Delete the organization
        session.delete(organization)
        session.commit()

        return {"message": "Organization deleted successfully"}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

# @ar.get("/get-organization-hierarchy/")
# async def get_organization_hierarchy(
#     session: SessionDep,
# tenant: str,
#     current_user: UserDep,
#     scope_group: int = Body(...),
# ):
#     try:
#         if not check_permission(
#             session, "Read", "Organization", current_user
#             ):
#             raise HTTPException(
#                 status_code=403, detail="You Do not have the required privilege"
#             )
#         scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == scope_group)).first()
#         if not scope_group:
#             raise HTTPException(status_code=404, detail="Scope group not found")

#         hierarchy = get_hierarchy(scope_group, session)
        
#         return {
#             "scope_group": scope_group.name,
#             "hierarchy": hierarchy
#         }
#     except Exception as e:
traceback.print_exc()
#         raise HTTPException(status_code=400, detail=str(e))
    
