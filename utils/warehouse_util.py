from fastapi import Depends, HTTPException, status, Path, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from sqlmodel import select
from models.Account import User
from models.Warehouse import Warehouse, WarehouseGroup, WarehouseGroupLink, WarehouseStoreAdminLink
from db import get_session

from typing import Annotated, Union, List
from sqlmodel import Session, select
from models.Account import User,AccessPolicy


import traceback



def check_warehouse_permission(
    session: Session,
    policy_type: str,
    warehouse_id: int,
    user: User,
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
        print(f"Checking permission for user_id={user.id}, username={user.username}, warehouse={warehouse_id}, policy={policy_type}")

       

        user = session.exec(select(User).where(User.id == user.id)).first()
        if not user or not user.warehouse_groups:
            print("User not found or has no warehouse group")
            return False

        warehouse_group_ids = [group.id for group in user.warehouse_groups]

        linked_group_ids = session.exec(
            select(WarehouseGroupLink.warehouse_group_id)
            .where(WarehouseGroupLink.warehouse_id == warehouse_id)
        ).all()

        filtered_groups = [group for group in user.warehouse_groups if group.id in linked_group_ids]
        print("filtered groups: ", filtered_groups)
        if not filtered_groups:
            print("User has no warehouse group for the associated warehouse")
            return False

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

        # Get the minimum access level from all the filtered groups
        group_access_levels = [
            access_levels.get(group.access_policy, 0)  # .value if AccessPolicy is Enum
            for group in filtered_groups
        ]
        print("all:", group_access_levels)
        lowest_access_level = min(group_access_levels)

        print(f"Lowest access level across all matched groups: {lowest_access_level}")
        print(f"Required access level: {required_access_level}")

        #  Allow access only if the lowest access level permits the operation
        if lowest_access_level & required_access_level:
            return True

        return False

    except Exception as e:
        print(f"Error in check_permission: {e}")
        traceback.print_exc()
        return False