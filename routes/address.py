import traceback
from fastapi import Depends, HTTPException
from typing import Annotated
from fastapi.routing import APIRouter
from models.viewModel.LocationViewModel import LocationRead
from sqlmodel import and_, select, Session
from sqlalchemy.orm import selectinload

from db import get_session
from models.Location import Address, Location
from utils.address_util import check_address
from utils.auth_util import get_current_user

SessionDep = Annotated[Session, Depends(get_session)]
# UserDep = Annotated[dict, Depends(get_current_user)]

AddressRouter = ar = APIRouter()


@ar.post("/create-address")
async def create_address(session: SessionDep, address: Address):
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
        address_db = check_address(session, address)
        return address_db
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@ar.get("/addresses")
async def get_addresses(session: SessionDep) -> list[Address]:
    """
    Retrieve all addresses from the database.

    Args:
        session (SessionDep): Database session.

    Returns:
        list[Address]: A list of Address objects.
        If empty it returns an empty list. []
    """
    try:
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
    
@ar.post("/create-location")
async def create_location(
    session: SessionDep, location: Location
):
    """
    Create a new location in the database.

    Args:
        session (SessionDep): Database session.
        location (Location): The Location object to create.

    Returns:
        Location: The created Location object.

    Raises:
        HTTPException: 400 if there is an error during creation.
    """
    try:
        location.id = None
        session.add(location)
        session.commit()
        session.refresh(location)
        return location
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@ar.get("/locations")
async def get_locations(session: SessionDep) -> list[LocationRead]:
    """
    Retrieve all locations from the database.

    Args:
        session (SessionDep): Database session.

    Returns:
        list[Location]: A list of Location objects.
        If empty it returns an empty list. []
    """
    statement = select(Location).options(selectinload(Location.address_rel))
    locations = session.exec(statement).all()


    return locations