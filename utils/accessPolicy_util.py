from fastapi import Depends, HTTPException, status
from typing import Annotated
from sqlmodel import Session, select


from models.user import User, Role, Module, AccessPolicy, RoleModulePermission
from models.auth import get_current_user
from db import get_session

# SessionDep = Annotated[Session, Depends(get_session)]

def check_permission(module: str, required: AccessPolicy):
    def dependency(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
        role = session.get(Role, user.role_id)
        module_obj = session.exec(select(Module).where(Module.name == module)).first()
        perm = session.exec(
            select(RoleModulePermission)
            .where(RoleModulePermission.role_id == role.id)
            .where(RoleModulePermission.module_id == module_obj.id)
        ).first()

        if not perm or perm.permission not in get_allowed_permissions(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permission: requires '{required}' for '{module}'"
            )
    return dependency

def get_allowed_permissions(required: AccessPolicy) -> list[str]:
    hierarchy = {
        "view": ["view", "edit", "contribute", "manage"],
        "edit": ["edit", "contribute", "manage"],
        "contribute": ["contribute", "manage"],
        "manage": ["manage"]
    }
    return hierarchy[required]
