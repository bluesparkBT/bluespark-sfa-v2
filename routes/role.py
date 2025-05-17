from typing import Annotated, Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends, Body, Path, status
from sqlmodel import Session, select


from db import SECRET_KEY, get_session
from models.Account import AccessPolicy, Role, RoleModulePermission, User, ScopeGroup, ScopeGroupLink
from models.Account import ModuleName as modules
from utils.auth_util import get_tenant, get_current_user, check_permission
from utils.model_converter_util import get_html_types
from utils.util_functions import validate_name
from utils.get_hierarchy import get_organization_ids_by_scope_group


RoleRouter = rr = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


@rr.get("/roles")
async def get_roles(
    session: SessionDep,
    tenant: str, 
    current_user: UserDep,
):
   
    try:
        if not check_permission(
            session, "Read", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        roles = session.exec(
            select(Role).where(Role.organization_id.in_(organization_ids))
        ).all()
        
        
        filtered_data = []                
        if not roles:
            raise HTTPException(status_code=404, detail="Role not found")
        for role in roles:
            permissions = ""
            for perm in role.permissions:
                if(perm.access_policy != "deny"):
                    permissions += perm.module+"("+perm.access_policy+"),"
            filtered_data.append({
                "id": role.id,
                "role_name": role.name,
                "roles": permissions
            })
     
        return filtered_data
 
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@rr.get("/my-role")
async def get_my_role(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
):
    try:
        if not check_permission(
            session, "Read", ["Administrative", "Role", "Service Provider"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        user = session.exec(select(User).where(User.id ==current_user.id)).first()

        if not user or not user.role_id:
            raise HTTPException(status_code=404, detail="User or assigned role not found")
        
        role = session.exec(select(Role).where(Role.id == user.role_id)).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        permissions = [
            perm for perm in role.permissions if perm.module is not None
        ]

        return {
            "id": role.id,
            "role_name": role.name,
            **{  
                perm.module: perm.access_policy
                for perm in permissions
            }     
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@rr.get("/role/{id}")
async def create_role(
    session: SessionDep,
    id: int,
    tenant: str,
    current_user: UserDep,
):
    try:
        if not check_permission(
            session, "Read", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        role = session.exec(select(Role).where(Role.id == id)).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
       
        return {"id": role.id, "name": role.name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@rr.get("/roles-form")
async def form_roles(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
):
    try:
        if not check_permission(
            session, "Read", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        policy_type =  {i.value: i.value for i in AccessPolicy}
        print(policy_type)
        role = {
            "id":"",
            "name":"",
        }
        
        return {"data": role, "html_types": get_html_types("role")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@rr.post("/create-role")
async def create_role(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,    
    role_data: Dict[str, Any] = Body(...),

): 
    try:
        if not check_permission(
            session, "Create", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
       
        role_name = role_data.get("name")

        if validate_name(role_name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name is not valid",
        )
        
        #create role
        role = Role(
            name=role_name,
            organization_id = current_user.organization_id
        )


        session.add(role)
        session.commit()
        session.refresh(role)
   
        #create role module permission
        for module in modules:
            role_module_permission= RoleModulePermission(
                id=None,
                role_id=role.id,
                module=module.value,
                access_policy=AccessPolicy.deny
            )

            session.add(role_module_permission)
            session.commit()
            session.refresh(role_module_permission)
 
        return role.id
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
           
@rr.get("/modules-form")
async def form_modules(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
):
    try:
        if not check_permission(
            session, "Read", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        policy_type =  {i.value: i.value for i in AccessPolicy}
        modules_dict =  {i.value: i.value for i in modules}
        print(policy_type)
        role = {
            "role_id":"",
            "module":modules_dict,
            "policy":policy_type,
        }
        
        return {"data": role, "html_types": get_html_types("policy")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@rr.post("/update-role-module")
async def update_role(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,    
    role_id: int = Body(...),
    module: str = Body(...),
    policy: str = Body(...),

):
    try:
        if not check_permission(
            session, "Update", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        role_module_permission = session.exec(select(RoleModulePermission)
                                    .where((RoleModulePermission.role_id == role_id)&
                                          (RoleModulePermission.module == module))).first()
        role_module_permission.module = module
        role_module_permission.access_policy = policy

        session.add(role_module_permission)
        session.commit()
        session.refresh(role_module_permission)
     
       
        return "Role permission updated successfully"
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@rr.put("/update-role")
async def update_role(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,

    name: str = Body(...) ,
    id: int = Body(...),
):
    try:
        if not check_permission(
            session, "Update", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        role = session.exec(select(Role).where(Role.id== id)).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
      
        if validate_name(name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name is not valid",
        )

        role.name = name
        session.add(role)
        session.commit()
        session.refresh(role)
        return role.id
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@rr.delete("/delete-role/{id}")
async def delete_role(
    session: SessionDep,
    id: int,    
    tenant: str,
    current_user: UserDep,
):

    try:   
        if not check_permission(
            session, "Delete", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
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