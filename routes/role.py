from typing import Annotated, Any, Dict
from fastapi import APIRouter, HTTPException, Depends, Body, status
from sqlmodel import Session, select


from db import SECRET_KEY, get_session
from models.Account import Module, Role, RoleModulePermission, User
from utils.auth_util import get_current_user
from utils.util_functions import validate_name


RoleRouter = rr = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]




# @rr.get("/roles")
# async def get_roles(
#     session: SessionDep,
#     current_user: UserDep,
# ):
#     """
#     Retrieve all roles.

#     Args:
#         None

#     Returns:
#         List[Role]: List of all roles.

#     Raises:
#         HTTPException: If there is an error during the database operation.
#     """
#     try:
#         if not check_policy(session, "Read", "Admin", current_user.get("user")):
#             raise HTTPException(
#                 status_code=400, detail="You Do not have the required rrivilege"
#             )
#         roles = session.exec(select(Role)).all()
#         if roles == []:
#             return roles

#         for role in roles:
#             for key, value in role.model_dump().items():
#                 if key == "role_name" or key == "id":
#                     continue
#                 setattr(role, key, convert_rrivilege_level_to_crud(value))
#         roles_json = []
#         for role in roles:
#             role_dict = role.model_dump()
#             ordered_role = {
#                 "id": role_dict.pop("id"),
#                 "role_name": role_dict.pop("role_name"),
#             }
#             ordered_role.update(role_dict)
#             roles_json.append(ordered_role)
#         return roles_json
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))


# @rr.get("/role/{id}")
# async def get_role(session: SessionDep, current_user: UserDep, id: int):
#     try:
#         db_role = session.exec(select(Role).where(Role.id == id)).first()
#         role = Role()
#         for key, value in db_role.model_dump().items():
#             if key == "role_name" or key == "id":
#                 continue
#             v = convert_rrivilege_level_to_crud_full(value)
#             setattr(db_role, key, v)
#         return db_role
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))


@rr.get("/my-roles")
async def get_my_role(
    session: SessionDep,
    current_user: UserDep,
):
    try:
        user = session.exec(select(User).where(User.id ==current_user.get("user_id"))).first()

        if not user or not user.role_id:
            raise HTTPException(status_code=404, detail="User or assigned role not found")
        
        role = session.exec(select(Role).where(Role.id == user.role_id)).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")


        session.exec(select(RoleModulePermission).where(RoleModulePermission.role_id == role.id))

        permissions = {
            perm.module.name: perm.access_policy
            for perm in role.permissions if perm.module is not None
        }

        return {
            "id": role.id,
            "role_name": role.name,
            "permissions": permissions
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@rr.post("/create-role")
async def create_role(
    session: SessionDep,
    current_user: UserDep,
    role_data: Dict[str, Any] = Body(...) 
):
 
   
    try:
        #role_data={role_name:"", user:2, Category:"",Product:"",....}
        user_id = role_data.get("user")

        #check if user to which the role is going to be assigned to exist
        user = session.exec(
                select(User).where(User.id == user_id)
            ).first()
        
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User is not found",
        )

        role_name = role_data.get("role_name")

        if validate_name(role_name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name is not valid",
        )
        
        
        #create role
        role = Role(
            name=role_name,
            organization_id = current_user['organization']
        )


        session.add(role)
        session.commit()
        session.refresh(role)
   
        #create role module permission
        for key, value in role_data.items():
            if key == "role_name" or key == "id" or key == "user":
                continue
            module = session.exec(select(Module).where(Module.name == key)).first()
            if not module:
                raise HTTPException(
                    status_code=404,
                    detail=f"Module '{key}' not found"
                )
           
            role_module_permission= RoleModulePermission(
                role_id=role.id,
                module_id=module.id,
                access_policy=value
            )

            session.add(role_module_permission)
            session.commit()
            session.refresh(role_module_permission)

        # assign role to user
       
        user.role_id = role.id

        session.add(user)
        session.commit()
        session.refresh(user)

        return "Role "+role.name+" created"
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@rr.put("/update-role")
async def update_role(
    session: SessionDep,
    current_user: UserDep,
    role_data: Dict[str, Any] = Body(...) 
):
    try:
        user_id = role_data.get("user")

        #check if user to which the role is going to be assigned to exist
        user = session.exec(
                select(User).where(User.id == user_id)
            ).first()
        
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User is not found",
        )
    
        role = session.exec(select(Role).where(Role.id == role_data.get("id"))).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        role_name = role_data.get("role_name")

        if validate_name(role_name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name is not valid",
        )
        
        role.name = role_name

        for key, value in role_data.items():
            if key == "role_name" or key == "id" or key == "user":
                continue
            module = session.exec(select(Module).where(Module.name == key)).first()
            if not module:
                raise HTTPException(
                    status_code=404,
                    detail=f"Module '{key}' not found"
                )
            role_module_permission = session.exec(select(RoleModulePermission)
            .where((RoleModulePermission.module_id == module.id) & 
                   (RoleModulePermission.role_id == role.id)&
                   (user.role_id == role.id))).first()
        
            role_module_permission.access_policy = value
            session.add(role_module_permission)
            session.commit()
            session.refresh(role_module_permission)


       
        return "Role "+role.name+" updated"
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@rr.delete("/delete-role/{id}")
async def delete_role(
    session: SessionDep,
    current_user: UserDep,
    id: int,
):

    try:
       
        role = session.exec(select(Role).where(Role.id == id)).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        assigned_users = session.exec(select(User).where(User.role_id == id)).all()

        for user in assigned_users:
            user.role_id = None
            session.add(user)  # mark for update

        session.commit()

        assigned_role_module= session.exec(select(RoleModulePermission).where(RoleModulePermission.role_id == id)).all()

        for role_module in assigned_role_module:
            session.delete(role_module) 
            session.commit() 

        
        
        session.delete(role)
        session.commit()
        return "Role deleted successfully"
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

