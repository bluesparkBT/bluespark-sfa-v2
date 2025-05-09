from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select


from db import SECRET_KEY, get_session
from models.Account import Role, UserRole
from utils.auth_util import get_current_user
from utils.form_db_fetch import fetch_role_name_and_id, fetch_username_and_id
from utils.model_converter_util import get_html_types
from utils.policy_util import (
    check_policy,
    convert_policy_list_to_privilege_level,
    convert_privilege_level_to_crud,
    convert_privilege_level_to_crud_full,
)

RoleRouter = rr = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]




@rr.get("/roles")
async def get_roles(
    session: SessionDep,
    current_user: UserDep,
):
    """
    Retrieve all roles.

    Args:
        None

    Returns:
        List[Role]: List of all roles.

    Raises:
        HTTPException: If there is an error during the database operation.
    """
    try:
        if not check_policy(session, "Read", "Admin", current_user.get("user")):
            raise HTTPException(
                status_code=400, detail="You Do not have the required rrivilege"
            )
        roles = session.exec(select(Role)).all()
        if roles == []:
            return roles

        for role in roles:
            for key, value in role.model_dump().items():
                if key == "role_name" or key == "id":
                    continue
                setattr(role, key, convert_rrivilege_level_to_crud(value))
        roles_json = []
        for role in roles:
            role_dict = role.model_dump()
            ordered_role = {
                "id": role_dict.pop("id"),
                "role_name": role_dict.pop("role_name"),
            }
            ordered_role.update(role_dict)
            roles_json.append(ordered_role)
        return roles_json
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@rr.get("/role/{id}")
async def get_role(session: SessionDep, current_user: UserDep, id: int):
    try:
        db_role = session.exec(select(Role).where(Role.id == id)).first()
        role = Role()
        for key, value in db_role.model_dump().items():
            if key == "role_name" or key == "id":
                continue
            v = convert_rrivilege_level_to_crud_full(value)
            setattr(db_role, key, v)
        return db_role
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@rr.get("/my-roles")
async def get_my_role(
    session: SessionDep,
    current_user: UserDep,
):
    try:
        db_role: list[Role] = session.exec(
            select(Role)
            .join(UserRole, UserRole.role == Role.id)
            .where(UserRole.user == current_user.get("user"))
        ).all()
        if not db_role:
            raise HTTPException(status_code=404, detail="Role not found")
        role = Role()
        for r in db_role:
            for key, value in r.model_dump().items():
                if key in ["id", "role_name"]:
                    continue
                if not getattr(role, key) or value > getattr(role, key):
                    setattr(role, key, value)
        crud_role = Role()
        for key, value in role.model_dump().items():
            if key == "role_name" or key == "id":
                continue
            setattr(crud_role, key, convert_rrivilege_level_to_crud(value))
        return crud_role
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@rr.post("/create-role")
async def create_role(
    session: SessionDep,
    current_user: UserDep,
    role: RoleViewModel,
):
    """
    Create a new role.

    Args:
        role (Role): The role to create.

    Returns:
        Role: The newly created role.

    Raises:
        HTTPException: If there is an error during the database operation.
    """

    try:
        if not check_policy(session, "Create", "Admin", current_user.get("user")):
            raise HTTPException(
                status_code=400, detail="You Do not have the required rrivilege"
            )

        db_role: Role = Role()
        db_role.role_name = role.role_name

        for key, value in role.model_dump().items():
            if key == "role_name" or key == "id":
                continue
            v = convert_policy_list_to_rrivilege_level(value)
            setattr(db_role, key, v)

        db_role.id = None
        session.add(db_role)
        session.commit()
        session.refresh(db_role)
        return db_role
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@rr.put("/update-role")
async def update_role(
    session: SessionDep,
    current_user: UserDep,
    role: RoleViewModel,
):
    """
    Update an existing role.

    Args:
        role (Role): The updated role data.

    Returns:
        Role: The updated role.

    Raises:
        HTTPException: If the role is not found or if there is an error during the database operation.
        400 if the role is Admin or Super Admin.
    """
    try:
        if not check_policy(session, "Update", "Admin", current_user.get("user")):
            raise HTTPException(
                status_code=400, detail="You Do not have the required rrivilege"
            )
        db_role = session.exec(select(Role).where(Role.id == role.id)).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        db_role.role_name = role.role_name

        for key, value in role.model_dump().items():
            if key == "role_name" or key == "id":
                continue
            v = convert_policy_list_to_rrivilege_level(value)
            setattr(db_role, key, v)

        session.add(db_role)
        session.commit()
        session.refresh(db_role)
        return db_role
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@rr.delete("/delete-role/{id}")
async def delete_role(
    session: SessionDep,
    current_user: UserDep,
    id: int,
):
    """
    Delete an existing role.

    Args:
        id (int): The ID of the role to delete.

    Returns:
        Role: The deleted role.

    Raises:
        HTTPException: If there is an error during the database operation.
    """
    try:
        if not check_policy(session, "Delete", "Admin", current_user.get("user")):
            raise HTTPException(
                status_code=400, detail="You Do not have the required privilege"
            )
        role = session.exec(select(Role).where(Role.id == id)).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        session.delete(role)
        session.commit()
        return "Role deleted successfully"
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

