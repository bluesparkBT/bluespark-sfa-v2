import bcrypt, jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, Path, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from sqlmodel import select
from models.Account import User
from db import get_session

from typing import Annotated, Union, List
from sqlmodel import Session
from models.Account import AccessPolicy, RoleModulePermission, Role, User, ModuleName
from sqlmodel import select
from typing import Literal
import hashlib
import traceback
import string
import random
import re

security = HTTPBearer()
SECRET_KEY = "secret_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90

SessionDep = Annotated[Session, Depends(get_session)]

# This assumes you've saved tenant in request.state via middleware
def get_tenant(
    request: Request,
    session: SessionDep,
) -> str:
    tenant = getattr(request.state, "tenant", None)
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant not found.")
     
    return tenant

def tenant_users(username: str, tenant_name: str) -> str:
    clean_tenant = re.sub(r"\s+", "_", tenant_name.strip().lower())
    return f"{clean_tenant}_{username}"

def extract_username(username: str, tenant_name: str) -> str:
    prefix = re.sub(r"\s+", "_", tenant_name.strip().lower())
    # prefix = f"{tenant_name.lower()}_"
    if username.startswith(prefix):
        return username[len(prefix):]
    raise ValueError("Username does not match the given tenant prefix.")

def get_tenant_hash(tenant_name: str) -> str:
    return hashlib.sha256(tenant_name.encode('utf-8')).hexdigest()

def verify_tenant(tenant_name: str, hashed_tenant_name: str) -> bool:
    return bcrypt.checkpw(tenant_name.encode(), hashed_tenant_name.encode())

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


def get_current_user(session: SessionDep,credentials: HTTPAuthorizationCredentials = Depends(security)):
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
        
        user_db = session.exec(select(User).where(User.username == username)).first()
        
        return user_db
    except InvalidTokenError:
        raise credentials_exception
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def generate_random_password(length: int = 12) -> str:
    """Generate a secure random password with uppercase, lowercase, digits, and punctuation."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.SystemRandom().choice(characters) for _ in range(length))

def check_permission(
    session: Session,
    policy_type: str,
    endpoint_groups: Union[str, List[str]],
    user: int,
) -> bool:
    """
    Checks if the user has the required access policy for one or more modules.

    Args:
        session (Session): DB session.
        policy_type (str): Required access policy level ('Create', 'Read', etc.).
        endpoint_groups (Union[str, List[str]]): Module name or list of modules.
        user (User): The current user object.

    Returns:
        bool: True if the user has access to any of the given modules.
    """
    try:
        print(f"Checking permission for user_id={user.id}, username={user.username}, modules={endpoint_groups}, policy={policy_type}")

        # Make sure it's a list
        if isinstance(endpoint_groups, str):
            endpoint_groups = [endpoint_groups]

        user = session.exec(select(User).where(User.id == user.id)).first()
        if not user or not user.role_id:
            print("User not found or has no role")
            return False

        role = session.exec(select(Role).where(Role.id == user.role_id)).first()
        if not role:
            print("Role not found")
            return False

        # Prepare access levels and policy map
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
            "Delete": 3,
        }

        required_access_level = 1 << crud_digit[policy_type]

        # Check permission for each module
        for endpoint_group in endpoint_groups:
            if endpoint_group not in [moduleName.value for moduleName in ModuleName]:
                print(f"Module '{endpoint_group}' not found in enums")
                continue

            permission = session.exec(
                select(RoleModulePermission)
                .where(RoleModulePermission.role_id == role.id)
                .where(RoleModulePermission.module == endpoint_group)
            ).first()

            if not permission:
                print(f"No permission record found for module '{endpoint_group}'")
                continue

            user_access_level = access_levels[permission.access_policy]
            print(f"User Access Level for {endpoint_group}: {user_access_level}, Required: {required_access_level}")

            if user_access_level & required_access_level:
                return True

        # If none of the modules matched
        return False

    except Exception as e:
        print(f"Error in check_permission: {e}")
        traceback.print_exc()
        return False