from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
import jwt
from sqlmodel import Session, select
from db import SECRET_KEY, get_session
from models.User import User

security = HTTPBearer()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 2
REFRESH_TOKEN_EXPIRE_DAYS = 30
SessionDep = Annotated[Session, Depends(get_session)]
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# async def auth_middleware(request: Request, call_next):
#     token = request.cookies.get("access_token")
#     if token and token.startswith("Bearer "):
#         token = token.split(" ")[1]  # Extract the actual token
#         request.headers.__dict__["_list"].append(
#             (b"authorization", f"Bearer {token}".encode())
#         )
#     response = await call_next(request)
#     return response


def verify_password(plain_password, hashed_password):
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the plain password matches the hashed password, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Hash a password using bcrypt.

    Args:
        password (str): The password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def get_user(session: SessionDep, username: str):
    """
    Retrieve a user from the database by username.

    Args:
        session (SessionDep): The database session.
        username (str): The username of the user to retrieve.

    Returns:
        User: The user object if found, None otherwise.

    Raises:
        HTTPException: If the user is not found.
    """
    try:
        user = session.exec(select(User).where(User.username == username)).first()
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def authenticate_user(session: SessionDep, username: str, password: str):
    """
    Authenticate a user by verifying the username and password.

    Args:
        session (SessionDep): The database session.
        username (str): The username of the user to authenticate.
        password (str): The password of the user to authenticate.

    Returns:
        User: The user object if authentication is successful, None otherwise.
    """
    user: User = get_user(session, username)
    if not user:
        return None
    if not verify_password(password + user.username, user.hashedPassword):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Create a JWT access token.

    Args:
        data (dict): The data to encode in the token.
        expires_delta (timedelta, optional): The expiration time of the token. Defaults to 15 minutes.

    Returns:
        str: The encoded JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get the current user from the JWT token in the Authorization header.

    Args:
        credentials (HTTPAuthorizationCredentials, optional): The authorization credentials. Defaults to Depends(security).

    Returns:
        dict: The payload of the JWT token, which contains user information.

    Raises:
        HTTPException: If the token is invalid or the user cannot be authenticated.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        return payload
    except InvalidTokenError:
        raise credentials_exception
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
