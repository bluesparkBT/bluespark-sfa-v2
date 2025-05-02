import base64
from datetime import datetime
import os
from typing import Annotated, Optional
from fastapi import APIRouter, Body, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import jwt
from sqlmodel import Session, and_, select
from models.Location import Address
from utils.address_util import check_address
from utils.auth_util import (
    ALGORITHM,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)

from db import SECRET_KEY, get_session
from models.User import Gender, IdType, User
# from models.viewModel.authViewModel import Login, UserCreation, UserUpdate

# from utils.model_converter_util import get_html_types

from dotenv import load_dotenv

load_dotenv()
ENV = os.getenv("ENV")
AuthenticationRouter = r = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
# UserDep = Annotated[dict, Depends(get_current_user)]

@r.post("/create-user")
async def admin_create_user(
    session: SessionDep,
    # current_user: UserDep,
    fullname: str = Body(...),
    username: str = Body(...),
    password: str = Body(...),
    email: Optional[str] = Body(None),
    phone_number: str = Body(...),
    date_of_birth: Optional[datetime] = Body(None),
    date_of_joining: Optional[datetime] = Body(None),
    salary: Optional[float] = Body(None),
    position: Optional[str] = Body(None),
    id_type: Optional[IdType] = Body(None),
    id_number: Optional[str] = Body(None),
    gender: Optional[Gender] = Body(None, description="The gender of the user"),
    country: str = Body("Ethiopia"),
    city: str = Body(...),
    sub_city: str = Body(...),
    woreda: str = Body(...),
    landmark: Optional[str] = Body(None),
    # role: List[int] = Body(...) # Assuming role IDs
):
    """
    Create a new user account along with an associated address record.

    Attributes:

        id (Optional[int]): Unique identifier of the user (primary key).
        fullname (str): The full name of the user (indexed).
        username (str): The username of the user (indexed and unique).
        email (Optional[str]): The email address of the user (indexed).
        phone (str): The phone number of the user (indexed).
        password (str): The password of the user.
        date_of_birth (Optional[datetime]): The date of birth of the user.
        date_of_joining (Optional[datetime]): The date the user joined the system.
        salary (Optional[float]): The salary of the user.
        position (Optional[str]): The job position of the user.
        id_type (Optional[IdType]): The type of identification document.
        id_number (Optional[str]): The identification number.
        gender (Optional[Gender]): The gender of the user.
        country (str): The country of the address.
        city (str): The city of the address.
        sub_city (str): The sub-city of the address.
        woreda (str): The woreda of the address.
        landmark (Optional[str]): A notable landmark near the address.
        # role (List[int]): List of role IDs for the new user.

    Returns:

        User: The created user record.

    Raises:

        HTTPException: 400 if the user cannot be created due to insufficient privileges or other errors.
    """
    try:
        # if not check_policy(
        #     session, PolicyType.create_access, "Admin", current_user.get("user")
        # ):
        #     raise HTTPException(
        #         status_code=400, detail="You Do not have the required privilege"
        #     )

        address = Address(
            id=None,
            country=country,
            city=city,
            sub_city=sub_city,
            woreda=woreda,
            landmark=landmark,
        )
        db_address = check_address(session, address)
        user = User(
            id=None,
            fullname=fullname,
            username=username,
            email=email,
            phone=phone_number,
            hashedPassword=get_password_hash(password + username),
            date_of_birth=date_of_birth,
            date_of_joining=date_of_joining,
            salary=salary,
            position=position,
            id_type=id_type,
            id_number=id_number,
            gender=gender,
            address=db_address.id,
        )
        session.add(user)
        session.commit()

        # for r in role:
        #     user_role: UserRole = UserRole(
        #         user=user.id,
        #         role=r,
        #     )
        #     session.add(user_role)

        #session.commit()

        session.refresh(user)
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))