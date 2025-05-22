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
from utils.model_converter_util import get_html_types
from utils.auth_util import check_permission

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

AddressRouter = ar = APIRouter()


@ar.get("/get-addresses")
async def get_addresses(session: SessionDep, current_user: UserDep, tenant: str) -> list[Address]:
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
            session, "Read", ["Administrative", "Address"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        addresses = session.exec(select(Address)).all()
        return addresses
    except Exception as e:
        error_details = traceback.format_exc()
        errorlog = ErrorLog(
            id=None,
            endpoint="/addresses",
            request_data=None,
            error_message=str(e),
            stack_trace=error_details,
        )
        session.add(errorlog)
        session.commit()
        raise HTTPException(
            status_code=400, detail="Internal Server Error, Please Try again"
        )

@ar.get("/get-address/{id}")
async def get_address_by_id(session: SessionDep, current_user: UserDep, tenant: str, id: int):
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
            session, "Read",["Address", "Administrative"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        address = session.exec(select(Address).where(Address.id == id)).first()
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")
        return address
    except HTTPException as e:
        raise e
    except Exception as e:
        error_details = traceback.format_exc()
        raise HTTPException(status_code=400, detail=error_details)

@ar.get("/address-form")
async def get_form_fields_address(session: SessionDep, current_user: UserDep, tenant: str):
    address = Address(
        id="",
        country="Ethiopia",
        city="",
        sub_city="",
        woreda="",
        landmark="",
    )

    return {
        "data": address,
        "html_types": get_html_types('address'),
    }

@ar.post("/create-address")
async def create_address(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    country: str = Body(...),
    city : str = Body(...),
    sub_city : str = Body(...),
    woreda : str = Body(...),
    landmark : str = Body(...),
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
            session, "Create", ["Address", "Administrative"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        new_address = Address(
            id = None,
            country = country,
            city = city,
            sub_city = sub_city,
            woreda = woreda,
            landmark = landmark
            
        )
        session.add(new_address)
        session.commit()
        
        return {"Address Created successfully."}
    except Exception as e:
        traceback.print.exc()
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Create address failed: {str(e)}")

@ar.put("/update-address/")
async def update_address(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int = Body(...),
    country: Optional[str] = Body(...),
    city: Optional[str] = Body(...),
    sub_city: Optional[str] = Body(...),
    woreda: Optional[str] = Body(...),
    landmark: Optional[str] = Body(...),
):
    """
    Update an existing address by ID.
    """
    try:
        # Check permissions first
        if not check_permission(session, "Update", ["Address", "Administrative"], current_user):
            raise HTTPException(status_code=403, detail="Permission denied")

        # Fetch address
        address = session.exec(select(Address).where(Address.id == id)).first()
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")

        # Update only if values are provided (this is safe since you use Body(...))
        address.country = country
        address.city = city
        address.sub_city = sub_city
        address.woreda = woreda
        address.landmark = landmark

        session.add(address)
        session.commit()
        session.refresh(address)

        return address

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Update failed: {str(e)}")

@ar.delete("/delete-address/{id}")
async def delete_address(
    id: int,
    session: SessionDep,
    current_user: UserDep,
    tenant: str
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
        # Check permissions first
        if not check_permission(session, "Update", ["Address", "Administrative"], current_user):
            raise HTTPException(status_code=403, detail="Permission denied")

        address = session.exec(select(Address).where(Address.id == id)).first()
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")
        
        session.delete(address)
        session.commit()
        return {"message": "Address deleted successfully"}
    
    except Exception as e:
        traceback.print.exc()
        raise HTTPException(status_code=400, detail=f"Deletion failed: {str(e)}")


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
    """
    Delete a location from the database.

    Args:
        session (SessionDep): Database session.
        id (int): The ID of the location to delete.

    Returns:
        dict: A message indicating successful deletion.

    Raises:
        HTTPException: 404 if the location is not found.
        HTTPException: 400 if there is an error during deletion.
    """

    location = session.exec(select(Location).where(Location.id == id)).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    try:
        session.delete(location)
        session.commit()
        return {"message": "Location deleted successfully"}
    except Exception as e:
        traceback.print.exc()
        raise HTTPException(status_code=400, detail=str(e))