import bcrypt, jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from sqlmodel import select
from models.Account import User
from db import get_session

from typing import Annotated
from sqlmodel import Session
from models.Account import AccessPolicy, RoleModulePermission, Role, User
from sqlmodel import select
from typing import Literal


security = HTTPBearer()
SECRET_KEY = "secret_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90

SessionDep = Annotated[Session, Depends(get_session)]


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(data: dict, expires_delta: timedelta | None = None):
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
    



PolicyType = Literal["deny", "view", "edit", "contribute", "manage"]

def check_accessPolicy(
    session: SessionDep, 
    policy_type: PolicyType, 
    endpoint_group: str, 
    user_id: int
) -> bool:
    """
    Checks if the user has the required privilege level to access a certain endpoint.

    Args:
        session (SessionDep): Database session.
        policy_type (PolicyType): The required access policy (e.g., "view", "edit").
        endpoint_group (str): The module or endpoint group (e.g., "Product", "Sales").
        user_id (int): The ID of the user.

    Returns:
        bool: True if the user has the required privilege, False otherwise.
    """
    try:
        # Fetch the user and their role
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user or not user.role_id:
            return False  # User does not exist or has no assigned role

        # Fetch the role and its permissions
        role = session.exec(select(Role).where(Role.id == user.role_id)).first()
        if not role:
            return False  # Role does not exist

        # Fetch the module permission for the specified endpoint group
        permission = session.exec(
            select(RoleModulePermission)
            .join(Module, RoleModulePermission.module_id == Module.id)
            .where(
                RoleModulePermission.role_id == role.id,
                Module.name == endpoint_group
            )
        ).first()

        if not permission:
            return False  # No permission found for the specified module

        # Check if the user's access policy meets or exceeds the required policy
        access_levels = {
            AccessPolicy.deny: 0,
            AccessPolicy.view: 1,
            AccessPolicy.edit: 2,
            AccessPolicy.contribute: 3,
            AccessPolicy.manage: 4,
        }

        user_access_level = access_levels[permission.access_policy]
        required_access_level = access_levels[AccessPolicy(policy_type)]

        return user_access_level >= required_access_level

    except Exception as e:
        # Log the error or handle it as needed
        print(f"Error checking access policy: {e}")
        return False