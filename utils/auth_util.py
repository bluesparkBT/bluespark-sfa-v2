import bcrypt, jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from sqlmodel import select
from models.Account import User
from db import get_session

from typing import Annotated, Dict
from sqlmodel import Session
from models.Account import AccessPolicy, RoleModulePermission, Role, User, ModuleName
from sqlmodel import select
from typing import Literal
import traceback
import string
import random

security = HTTPBearer()
SECRET_KEY = "secret_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90

SessionDep = Annotated[Session, Depends(get_session)]

def get_tenant(tenant: str = Path(...)):
    # Validate tenant (optional)
    # e.g., check if tenant exists in DB
    return tenant

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
    


def generate_random_password(length: int = 12) -> str:
    """Generate a secure random password with uppercase, lowercase, digits, and punctuation."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.SystemRandom().choice(characters) for _ in range(length))

def check_permission(
    session: Session,
    policy_type: str,
    endpoint_group: str,
    user_id: int,
) -> bool:
    """
    Checks if the user has the required access policy for a specific module.

    Args:
        session (Session): DB session.
        policy_type (str): Required access policy level (e.g., 'view', 'edit').
        endpoint_group (str): The system module (e.g., 'Users', 'Sales').
        user_id (int): ID of the user making the request.

    Returns:
        bool: True if access is allowed, False otherwise.
    """
    try:
        # Debug step-by-step checks
        print(f"Checking permission for user_id={user_id}, module={endpoint_group}, policy={policy_type}")
        
        user = session.exec(select(User).where(User.id == user_id['user_id'])).first()
        if not user or not user.role_id:
            print("User not found or has no role")
            return False

        role = session.exec(select(Role).where(Role.id == user.role_id)).first()
        if not role:
            print("Role not found")
            return False

        if endpoint_group in [moduleName.value for moduleName in ModuleName]:
            module = endpoint_group
        else:
            print(f"Module '{endpoint_group}' not found")
            return False
        
        print(module)

        permission = session.exec(
            select(RoleModulePermission)
            .where(
                RoleModulePermission.role_id == role.id,
                RoleModulePermission.module == module,
            )
        ).first()

        if not permission:
            print("No permission record found")
            return False

        # Access level comparison
        access_levels = {
            "deny": 0,
            "view": 2,
            "edit": 6,
            "contribute": 7,
            "manage": 15,
        }
        
        
        crud_digit = {
            "Create": 0,
            "Read": 1,
            "Update": 2,
            "Delete": 3
        }

        user_access_level = access_levels[permission.access_policy]
        print("Access Level User",access_levels[permission.access_policy], user_access_level)
      
        required_access_level = 1 << crud_digit[policy_type] 
        print("Access Level Required",crud_digit[policy_type], required_access_level)
      
        if user_access_level & required_access_level:
            return True
        else:
            return False

    except Exception as e:
        print(f"Error in check_permission: {e}")
        traceback.print_exc()
        return False
