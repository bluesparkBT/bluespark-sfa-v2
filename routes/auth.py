import base64
from datetime import datetime, timedelta
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
    ACCESS_TOKEN_EXPIRE_DAYS,
    REFRESH_TOKEN_EXPIRE_DAYS,
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

@r.post("/login")
async def login(session: SessionDep, username: str=Body(...),password: str=Body(...)):
    """Authenticate a user with their username and password.

    Args:
        session (SessionDep): Database session
        username (str): username of the user
        password (str): password of the user

    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 400 if other error occurs

    Returns:
        JSON: access token and refresh token
    """
    try:
        user: User = authenticate_user(session=session, username=username, password=password);
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "username": user.id,
            },
            expires_delta=access_token_expires,
        )

        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = create_access_token(
            data={
                "sub": user.username,
                "type": "refresh token"
            },
            expires_delta=refresh_token_expires
        )

        return {"access_token": access_token, "refresh_token": refresh_token}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
          

@r.post("/create-user")
async def create_user(
    session: SessionDep,
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
    """Create a user

    Args:
        session (SessionDep): _description_
        fullname (str, optional): _description_. Defaults to Body(...).
        username (str, optional): _description_. Defaults to Body(...).
        password (str, optional): _description_. Defaults to Body(...).
        email (Optional[str], optional): _description_. Defaults to Body(None).
        phone_number (str, optional): _description_. Defaults to Body(...).
        date_of_birth (Optional[datetime], optional): _description_. Defaults to Body(None).
        date_of_joining (Optional[datetime], optional): _description_. Defaults to Body(None).
        salary (Optional[float], optional): _description_. Defaults to Body(None).
        position (Optional[str], optional): _description_. Defaults to Body(None).
        id_type (Optional[IdType], optional): _description_. Defaults to Body(None).
        id_number (Optional[str], optional): _description_. Defaults to Body(None).
        gender (Optional[Gender], optional): _description_. Defaults to Body(None, description="The gender of the user").
        country (str, optional): _description_. Defaults to Body("Ethiopia").
        city (str, optional): _description_. Defaults to Body(...).
        sub_city (str, optional): _description_. Defaults to Body(...).
        woreda (str, optional): _description_. Defaults to Body(...).
        landmark (Optional[str], optional): _description_. Defaults to Body(None).

    Raises:
        HTTPException: 400 if the username already exists
        HTTPException: 400 if other exception occurs

    Returns:
        User: the user created
    """
    try:
        # Check if user already exists
        existing_user = session.exec(select(User).where(User.username == username)).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already registered",
            )

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
            address_id=db_address.id,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
