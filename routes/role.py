from typing import Annotated, Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends, Body, Path, status
from sqlmodel import Session, select


from db import SECRET_KEY, get_session
from models.Account import AccessPolicy, Role, RoleModulePermission, User, ScopeGroup, ScopeGroupLink
from models.Account import ModuleName as modules
from utils.auth_util import get_tenant, get_current_user, check_permission
from utils.model_converter_util import get_html_types
from utils.util_functions import validate_name, parse_enum
from utils.get_hierarchy import get_organization_ids_by_scope_group


RoleRouter = rr = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

#create role module permission
modules_to_grant = [
    modules.administrative.value,
    modules.address.value,
    modules.category.value,
    modules.dashboard.value,
    modules.deposit.value,
    modules.finance.value,
    modules.product.value,
    modules.penetration.value,
    modules.presales.value,
    modules.inheritance.value,
    modules.inventory_management.value,
    modules.order.value,
    modules.organization.value,
    modules.sales.value,
    modules.stock.value,
    modules.scope_group.value,
    modules.role.value,
    modules.route.value,
    modules.route_schedule.value,
    modules.trade_marketing.value,
    modules.territory.value,
    modules.point_of_sale.value,
    modules.users.value,
    modules.visit.value,
    modules.vehicle.value,
    modules.warehouse.value,
    modules.warehouse_stop.value,
    
]
mod = modules

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
                    permissions += f"<strong>{perm.module}</strong> ({perm.access_policy.value}), "
            filtered_data.append({
                "id": role.id,
                "role_name": role.name,
                "roles": permissions.rstrip(", ")
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
        role_module_permissions = session.exec(
            select(RoleModulePermission.module, RoleModulePermission.access_policy).where(
                RoleModulePermission.role_id == id
            )
        ).all()

        formatted_permissions = {
            module: access_policy.value
            for module, access_policy in role_module_permissions
        }

        
        print("role module perm", formatted_permissions)
       
        return {"id": role.id, "name": role.name, "permissions": formatted_permissions}
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
        # Check if current user is a super admin
        user_scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == current_user.scope_group_id)).first()
         
        # Filter modules, exclude "Service Provider" unless super admin
        if user_scope_group.scope_name == "Super Admin Scope":
            modules_dict = {i.value: i.value for i in modules}
        else:
            modules_dict = {
                i.value: i.value for i in modules if i.value != "Service Provider"
            }
        role = {
            "id":None,
            "name":"",
            "module":modules_dict,
            "policy":policy_type,
        }
        
        return {"data": role, "html_types": get_html_types("role")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@rr.post("/create-role")
async def create_role(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,    
    id:str|int  = Body(...),
    name: str = Body(...),
    module: str = Body(...),
    policy: str = Body(...),


): 
    try:
        if not check_permission(
            session, "Create", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        if(parse_enum(AccessPolicy,policy,"Policy") == None or parse_enum(mod,module,"Module") == None):
             raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Required field missing",
                )


        #check exisiting role
        print("id", id)
        role_id: int
        if(id !=""):
            role = session.query(Role).where(Role.id==id).first()

            
            if not role:
                if validate_name(name) == False:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Role name is not valid",
                )
                
                #create role
                role = Role(
                    name=name,
                    organization_id = current_user.organization_id
                )


                session.add(role)
                session.commit()
                session.refresh(role)
                role_id = role.id
            else:
                role_id = role.id
        else:
            #create role
            if validate_name(name) == False:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Role name is not valid",
            )
            role = Role(
                name=name,
                organization_id = current_user.organization_id
            )


            session.add(role)
            session.commit()
            session.refresh(role)
            role_id = role.id

        

        
   
        # grant module permissions from list of modules defined as modules_togrant
       
        role_module_permission = session.exec(select(RoleModulePermission)
                                    .where((RoleModulePermission.role_id == role_id)&
                                          (RoleModulePermission.module == module))).first()
        if(role_module_permission):
            role_module_permission.module = module
            role_module_permission.access_policy = policy
        else:
            role_module_permission= RoleModulePermission(
                    id=None,
                    role_id=role_id,
                    module=module,
                    access_policy=policy
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
        # Check if current user is a super admin
        user_scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == current_user.scope_group_id)).first()
         
        # Filter modules, exclude "Service Provider" unless super admin
        if user_scope_group.scope_name == "Super Admin Scope":
            modules_dict = {i.value: i.value for i in modules}
        else:
            modules_dict = {
                i.value: i.value for i in modules if i.value != "Service Provider"
            }
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
        if(role_module_permission):
            role_module_permission.module = module
            role_module_permission.access_policy = policy
        else:
            role_module_permission= RoleModulePermission(
                    id=None,
                    role_id=role_id,
                    module=module,
                    access_policy=policy
                )

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

    id:str|int  = Body(...),
    name: str = Body(...),
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
        print("module",module,"policy")
        if (parse_enum(AccessPolicy,policy, "policy") != None and parse_enum(mod,module,"Module") != None):
            print("in here")
            role_module_permission = session.exec(select(RoleModulePermission)
                                    .where((RoleModulePermission.role_id == id)&
                                          (RoleModulePermission.module == module))).first()
            if(role_module_permission):
                role_module_permission.module = module
                role_module_permission.access_policy = policy
            else:
                role_module_permission= RoleModulePermission(
                        id=None,
                        role_id=id,
                        module=module,
                        access_policy=policy
                    )

            session.add(role_module_permission)
            session.commit()
            session.refresh(role_module_permission)

    
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