import traceback
from fastapi import Depends, HTTPException, Body, APIRouter
from typing import Annotated, Optional
from fastapi.routing import APIRouter
from sqlmodel import and_, select, Session
from db import get_session
from models.Address import Address, Geolocation
from models.Utils import ErrorLog
from utils.address_util import check_address
from utils.auth_util import get_current_user
from models.viewModel.AddressView import AddressView as TemplateView
from utils.model_converter_util import get_html_types
from utils.auth_util import check_permission, check_permission_and_scope
from utils.form_db_fetch import get_organization_ids_by_scope_group, fetch_organization_id_and_name
from models.Account import Organization

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

AddressRouter = ar = APIRouter()

endpoint_name = "address"
db_model = Address

endpoint = {
    "get": f"/get-{endpoint_name}es",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",
    "update": f"/update-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}

role_modules = {   
    "get": ["Administrative", "Address"],
    "get_form": ["Administrative", "Address"],
    "create": ["Administrative", "Address"],
    "update": ["Administrative", "Address"],
    "delete": ["Administrative", "Address"],
}


@ar.get(endpoint['get'])
async def get_addresses(
    session: SessionDep, 
    current_user: UserDep, 
    tenant: str
):
    """
    Retrieve all addresses from the database.

    Args:
        session (SessionDep): Database session.

    Returns:
        list[Address]: A list of Address objects.
        If empty it returns an empty list. []
    """
    try:  
        if not check_permission(
            session, "Read",role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        entries_list = session.exec(
            select(db_model).where(db_model.organization.in_(organization_ids))
        ).all()

        if not entries_list:
            raise HTTPException(status_code=404, detail="Address not found")
        address_list = []
        for address in entries_list:
            temp = {
                "id": address.id,
                "country": address.country,
                "city": address.city,
                "sub_city": address.sub_city,
                "woreda": address.woreda,
            }
            if temp not in address_list:
                address_list.append(temp)

        return address_list

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

@ar.get(endpoint['get_by_id'] + "/{id}")
async def get_address_by_id(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int
):
    """
    Retrieve a specific address by its ID.

    Args:
        session (SessionDep): Database session.
        id (int): The ID of the address to retrieve.

    Returns:
        Address: The Address object if found.

    Raises:
        HTTPException: 404 if the address is not found.
    """
    try:
        if not check_permission(
            session, "Read",role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        entry = session.exec(select(db_model).where(db_model.id == id)).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Address not found")
        return entry
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    
@ar.get(endpoint['get_form'])
async def get_form_fields_address(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        if not check_permission(
            session, "Create",role_modules['get_form'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            ) 
        address = {
            "id": None,
            "country":"Ethiopia",
            "city":"",
            "sub_city":"",
            "woreda":"",
            "organization": fetch_organization_id_and_name(session, current_user)
        }

        return {"data": address, "html_types": get_html_types('address')}
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    
@ar.post(endpoint['create'])
async def create_template(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    valid: TemplateView,
):
    """
    Create a new address in the database.

    Args:
        session (SessionDep): Database session.
        address (Address): The Address object to create.

    Returns:
        Address: The created Address object.

    Raises:
        HTTPException: 400 if there is an error during creation.
    """
    try:
        if not check_permission(
            session, "Create",role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        # Create a new category entry from validated input
        new_entry = db_model.model_validate(valid)
        session.add(new_entry)
        session.commit()
        session.refresh(new_entry)

        return new_entry

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
      
@ar.put(endpoint['update'])
async def update_address(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    valid: TemplateView,
):
    """
    Update an existing address by ID.
    """
    try:
        # Check permissions first
        if not check_permission(
            session, "Update",role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        selected_entry = session.exec(
            select(db_model).where( db_model.id == valid.id)
        ).first()

        if not selected_entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")
       
        # Update only if values are provided (this is safe since you use Body(...))
        selected_entry.country = valid.country
        selected_entry.city = valid.city
        selected_entry.sub_city = valid.sub_city
        selected_entry.woreda = valid.woreda

        session.add(selected_entry)
        session.commit()
        session.refresh(selected_entry)

        return {"message": f"{endpoint_name} Updated successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

@ar.delete(endpoint['delete']+ "/{id}")
async def delete_address(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,
):
    """
    Delete an address from the database.

    Args:
        id (int): ID of the address to delete.
        session (SessionDep): Active DB session.
        current_user (UserDep): Current logged-in user.
        tenant (str): Tenant identifier (if multi-tenant setup).

    Returns:
        dict: A success message.

    Raises:
        HTTPException: If address is not found or deletion fails.
    """


    try:
        if not check_permission(
            session, "Delete",role_modules['delete'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        selected_entry = session.exec(
            select(db_model).where( db_model.id == id)
        ).first()

        if not selected_entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")
       
        session.delete(selected_entry)
        session.commit()
        return {"message": f"{endpoint_name} deleted successfully"}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")



# @ar.get("/form-location")
# async def get_form_fields_location(session: SessionDep, current_user: UserDep):
#     location = Geolocation(
#         id="",
#         name="",
#         address="",
#         latitude="",
#         longitude="",
#     )

#     return {
#         "data": location,
#         "html_types": get_html_types(Geolocation),
#     }

# @ar.get("/locations")
# async def get_locations(session: SessionDep, current_user: UserDep):
#     """
#     Retrieve all locations from the database.

#     Args:
#         session (SessionDep): Database session.

#     Returns:
#         list[Location]: A list of Location objects.
#         If empty it returns an empty list. []
#     """
#     locations = session.exec(select(Geolocation)).all()
#     return locations

# @ar.get("/location/{id}")
# async def get_location(session: SessionDep, current_user: UserDep, id: int):
#     """
#     Retrieve a specific location by its ID.

#     Args:
#         session (SessionDep): Database session.
#         id (int): The ID of the location to retrieve.

#     Returns:
#         Location: The Location object if found.

#     Raises:
#         HTTPException: 404 if the location is not found.
#     """
#     location = session.exec(select(Geolocation).where(Geolocation.id == id)).first()
#     if not location:
#         raise HTTPException(status_code=404, detail="Location not found")
#     return location

# @ar.post("/create-location")
# async def create_location(
#     session: SessionDep, current_user: UserDep,
# ):
#     """
#     Create a new location in the database.

#     Args:
#         session (SessionDep): Database session.
#         location (Location): The Location object to create.

#     Returns:
#         Location: The created Location object.

#     Raises:
#         HTTPException: 400 if there is an error during creation.
#     """
#     try:
#         location.id = None
#         session.add(location)
#         session.commit()
#         session.refresh(location)
#         return location
#     except Exception as e:
#         traceback.print.exc()
#         raise HTTPException(status_code=400, detail=str(e))

# @ar.put("/update-location")
# async def update_location(
#     session: SessionDep, current_user: UserDep, updatedLocation: Location
# ):
#     """
#     Update an existing location in the database.

#     Args:
#         session (SessionDep): Database session.
#         updatedLocation (Location): The Location object with updated information.

#     Returns:
#         Location: The updated Location object.

#     Raises:
#         HTTPException: 404 if the location is not found.
#         HTTPException: 400 if there is an error during update.
#     """
#     try:
#         existing_location = session.get(Location, updatedLocation.id)
#         if not existing_location:
#             raise HTTPException(status_code=404, detail="Location not found")
#         existing_location.name = updatedLocation.name
#         existing_location.address = updatedLocation.address
#         existing_location.latitude = updatedLocation.latitude
#         existing_location.longitude = updatedLocation.longitude
#         session.add(existing_location)
#         session.commit()
#         session.refresh(existing_location)
#         return existing_location
#     except Exception as e:
#         traceback.print.exc()
#         raise HTTPException(status_code=400, detail=str(e))

# @ar.delete("/delete-location/{id}")
# async def delete_location(session: SessionDep, current_user: UserDep, id: int):
    # """
    # Delete a location from the database.

    # Args:
    #     session (SessionDep): Database session.
    #     id (int): The ID of the location to delete.

    # Returns:
    #     dict: A message indicating successful deletion.

    # Raises:
    #     HTTPException: 404 if the location is not found.
    #     HTTPException: 400 if there is an error during deletion.
    # """

    # location = session.exec(select(Location).where(Location.id == id)).first()
    # if not location:
    #     raise HTTPException(status_code=404, detail="Location not found")
    # try:
    #     session.delete(location)
    #     session.commit()
    #     return {"message": "Location deleted successfully"}
    # except Exception as e:
    #     traceback.print.exc()
    #     raise HTTPException(status_code=400, detail=str(e))