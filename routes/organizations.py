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
from utils.get_hierarchy import get_organization_ids_by_scope_group, get_child_organization, get_heirarchy
from utils.form_db_fetch import fetch_organization_id_and_name, fetch_inheritance_group_id_and_name, fetch_address_id_and_name
import traceback

TenantRouter =tr= APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

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
            "organization": organization.organization_name,
            "owner": organization.owner_name,
            "logo": organization.logo_image,
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@tr.get("/get-organizations/")
async def get_organizations(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str,

):
    """
    Retrieve all organizations with their associated scope groups.
    """
    try:
        if not check_permission(
            session, "Read", "Organization", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        current_tenant_id = session.exec(select(Organization.id).where(Organization.id == current_user.organization_id)).first() if tenant == "provider" else session.exec(select(Organization.id).where(Organization.tenant_hashed == tenant)).first()
       
        
        organizations = get_heirarchy(session, current_tenant_id, None, current_user)
        
        if not organizations:
            raise HTTPException(status_code=404, detail="No organizations found")

        return organizations
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
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
        
        organizations = session.exec(select(Organization).where(Organization.parent_id == id)).all()

        if not organizations:
            return []

        organization_list = []

        for org in organizations:
            organization_list.append({
                "id": org.id,
                "organization": org.organization_name,
                "owner": org.owner_name,
                "logo": org.logo_image,
                "description": org.description,
                "organization_type": org.organization_type,
                "inheritance_group": org.inheritance_group,
                "parent_organization": org.parent_id,
                "scope_groups": [
                    {"id": sg.id, "scope_name": sg.scope_name}
                    for sg in org.scope_groups
                ]
            })

        return organization_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
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
            session, "Read", ["Organization", "Administrative"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
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
    
@tr.get("/get-organization/{id}")
async def get_organization(
    session: SessionDep,
    id: int,
    current_user: UserDep,
    tenant: str,
):
    try:
        if not check_permission(
            session, "Read", "Organization", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        organization = session.exec(select(Organization).where(Organization.id == id)).first()
        if not organization:
            raise HTTPException(status_code=404, detail="Role not found")
  
        return {
            "id": organization.id,
            "organization_name": organization.organization_name,
            "description": organization.description,
            "owner_name": organization.owner_name,
            "logo_image": organization.logo_image,
            "organization_type": organization.organization_type,
            "parent_organization": organization.parent_id
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
     
@tr.get("/organization-form/")
async def get_form_fields_organization(
    session: SessionDep,
    tenant: str,
    current_user: UserDep
):

    try:
        if not check_permission(
            session, "Read", "Organization", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        organization_data = {
            "id": "",
            "organization_name": "",
            "owner_name": "",
            "description": "",
            "logo_image": "",
            "parent_organization": fetch_organization_id_and_name(session, current_user),
            "organization_type" : {i.value: i.value for i in OrganizationType if i.value !="Service Provider"},
            "inheritance_group": fetch_inheritance_group_id_and_name(session, current_user),
            "address" : fetch_address_id_and_name(session, current_user),
            "landmark" : "",
            "latitude" : "",
            "longitude" : ""
            }
        

        return {"data": organization_data, "html_types": get_html_types('organization')}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@tr.post("/create-organization/")
async def create_organization(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    organization_name: str = Body(...),
    owner_name: str = Body(...),
    description: str = Body(...),
    logo_image: str = Body(...),
    parent_organization : int = Body(...),
    organization_type: str = Body(...),
    inheritance_group: Union[int, str, None] = Body(default=None),
    address : Optional[Union[int, str, None]] = Body(default=None),
    landmark : Optional[str] = Body(None),
    latitude : Optional[Union[float, str, None]] = Body(default=None),
    longitude: Optional[Union[float, str, None]] =Body(default=None)
):
    try:
        if not check_permission(
            session, "Create", "Organization", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        # existing_tenant = session.exec(select(Organization).where(Organization.organization_name == organization_name)).first()

        # if existing_tenant is not None:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Company already registered",
        # )
        
        #Check Validity
        if inheritance_group == "":
            inheritance_group = None

        if validate_name(owner_name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company owner name is not valid",
        )
        elif validate_image(logo_image) == False and logo_image is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Logo image is not valid",
        )
            
        if address == "" or address is None:
            address = None
            
        if latitude in ("", None):
            latitude = None
        else:
            latitude = float(latitude)

        if longitude in ("", None):
            longitude = None
        else:
            longitude = float(longitude)

        org_geolocation = None
        if latitude is not None and longitude is not None:
            org_geolocation = Geolocation(
                name=f"{organization_name} location",
                address_id=address,
                latitude=latitude,
                longitude=longitude
            )
            session.add(org_geolocation)
            session.commit()
            session.refresh(org_geolocation)


        organization = Organization(
            id = None,
            organization_name = organization_name,
            owner_name = owner_name,
            description = description,
            logo_image = logo_image,
            parent_id = parent_organization,
            organization_type = organization_type,
            inheritance_group = inheritance_group,
            address_id = address,
            landmark= landmark,
            location_id=org_geolocation.id if org_geolocation else None

        )
        
        session.add(organization)
        session.commit()
        session.refresh(organization)

        scope_group_link = ScopeGroupLink(
            scope_group_id=current_user.scope_group_id,
            organization_id=organization.id,
        )
        session.add(scope_group_link)
        session.commit()
        
        return {"message": "Organization created successfully", "organization": organization_name}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))           

@tr.put("/update-organization/")
async def create_organization(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str,

    id: int = Body(...),
    organization_name: str = Body(...),
    owner_name: str = Body(...),
    description: str = Body(...),
    logo_image: str = Body(...),
    organization_type: str = Body(...),    
    parent_organization: int | str = Body(...),
    inheritance_group: Union[int, str, None] = Body(default=None),
    address: Optional[str] = Body(default=None),
    landmark : Optional[str] = Body(None),
    latitude : Optional[str] = Body(None),
    longitude: Optional[str] =Body(None)
):

    try:
        if not check_permission(
            session, "Update", "Organization", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        existing_organization = session.exec(select(Organization).where(Organization.id == id)).first()
        if existing_organization is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization not found",
        )
        #Check Validity
        
        if validate_name(owner_name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company owner name is not valid",
        )
        elif validate_image(logo_image) == False and logo_image is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Logo image is not valid",
        )
        exisitng_org_geolocation = session.exec(select(Geolocation).where(Geolocation.id == existing_organization.address_id)).first()    
        if exisitng_org_geolocation:
            if latitude:
                exisitng_org_geolocation.latitude = latitude,
            if longitude:
                exisitng_org_geolocation.longitude = longitude
                
            session.add(exisitng_org_geolocation)
            session.commit()            
        else:
            org_geolocation = Geolocation(
                name = f"{organization_name} location",
                address_id = address,
                latitude = latitude,
                longitude = longitude
            )
            session.add(org_geolocation)
            session.commit()

        
        existing_organization.organization_name = organization_name
        existing_organization.owner_name = owner_name
        existing_organization.description = description
        if inheritance_group:
            existing_organization.inheritance_group= inheritance_group
        existing_organization.logo_image = logo_image
        existing_organization.organization_type = organization_type
        if parent_organization:
            existing_organization.parent_id = parent_organization
        if address:
            existing_organization.address_id = address
        if landmark:
            existing_organization.landmark = landmark,
            
        session.add(existing_organization)
        session.commit()
        session.refresh(existing_organization)
        
        return {"message": "Organization updated successfully", "organization": organization_name}
    
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
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

# @ar.get("/get-organization-hierarchy/")
# async def get_organization_hierarchy(
#     session: SessionDep,
# tenant: str,
#     current_user: UserDep,
#     scope_group_id: int = Body(...),
# ):
#     try:
#         if not check_permission(
#             session, "Read", "Organization", current_user
#             ):
#             raise HTTPException(
#                 status_code=403, detail="You Do not have the required privilege"
#             )
#         scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == scope_group_id)).first()
#         if not scope_group:
#             raise HTTPException(status_code=404, detail="Scope group not found")

#         hierarchy = get_hierarchy(scope_group, session)
        
#         return {
#             "scope_group": scope_group.scope_name,
#             "hierarchy": hierarchy
#         }
#     except Exception as e:
traceback.print_exc()
#         raise HTTPException(status_code=400, detail=str(e))
    
