import traceback
from typing import Annotated, Optional
from fastapi import APIRouter, HTTPException, Depends, Body, Path, status, Query
from sqlmodel import Session, select
from db import SECRET_KEY, get_session
from models.Account import (
    AccessPolicy,
    Role,
    RoleModulePermission,
    User,
    ScopeGroup)
from models.viewModel.AccountsView import RoleView as TemplateView
from models.Account import ModuleName as modules
from models.Account import SuperAdminModuleName as superAdminModules
from utils.auth_util import get_tenant, get_current_user, check_permission
from utils.model_converter_util import get_html_types
from utils.util_functions import validate_name, parse_enum
from utils.get_hierarchy import get_organization_ids_by_scope_group


RoleRouter = rr = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "role"
db_model = Role

endpoint = {
    "get": f"/get-{endpoint_name}s",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",
    "update": f"/update-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}

role_modules = {   
    "get": ["Administrative", "Role"],
    "get_form": ["Administrative", "Role"],
    "create": ["Administrative", "Role"],
    "update": ["Administrative", "Role"],
    "delete": ["Administrative"],
}

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
        if not user or not user.role:
            raise HTTPException(status_code=404, detail="User or assigned role not found")
        
        role = session.exec(select(Role).where(Role.id == user.role)).first()

        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        permissions = [
            perm for perm in role.permissions if perm.module is not None
        ]

        return {
            "id": role.id,
            "name": role.name,
            **{  
                perm.module: perm.access_policy
                for perm in permissions
            }     
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    
@rr.get(endpoint['get'])
def get_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:  
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        roles = session.exec(
            select(db_model).where(db_model.organization.in_(organization_ids))
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
                "name": role.name,
                "roles": permissions.rstrip(", ")
            })
        return filtered_data

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

@rr.get(endpoint['get_by_id'] + "/{id}")
def get_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int,
):
    try:
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        role = session.exec(select(Role).where(Role.id == id)).first()
        
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        role_module_permissions = session.exec(
            select(RoleModulePermission.module, RoleModulePermission.access_policy).where(
                RoleModulePermission.role == id
            )
        ).all()

        formatted_permissions = {
            module: access_policy.value
            for module, access_policy in role_module_permissions
        }       
        return {"id": role.id, "name": role.name, "module": role_module_permissions[0].module, "policy": role_module_permissions[0].access_policy,"permissions": formatted_permissions}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    
@rr.get(endpoint['get_form'])
def get_template_form(
    tenant: str,
    session: SessionDep,
    current_user: UserDep,
) :
    """   Retrieves the form structure for creating a new category.
    """
    try:
        # Check permission
        if not check_permission(
            session, "Create",role_modules['get_form'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            ) 
        policy_type =  {i.value: i.value for i in AccessPolicy}
        user_scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == current_user.scope_group)).first()
         
        if user_scope_group.name == "Super Admin Scope":
            modules_dict = {i.value: i.value for i in superAdminModules}
        else:
            modules_dict = {
                i.value: i.value for i in modules if i.value != "Service Provider"
            }
        role = {
            "id": None,
            "name":"",
            "module":modules_dict,
            "policy":policy_type,
            "permisssion": ""
        }
        
        return {"data": role, "html_types": get_html_types("role")}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

@rr.post(endpoint['create'])
def create_template(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    valid: TemplateView,
):
    try:
        
        if not check_permission(
            session, "Create", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        if(parse_enum(AccessPolicy, valid.policy,"Policy") == None or parse_enum(mod, valid.module,"Module") == None):
             raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Required field missing",
                )
        #check exisiting role
        print("role id", id)
        role_id: int
        if id:
            print("role is not None")
            role = session.query(Role).where(Role.id== valid.id).first()
            if not role:
                if validate_name(valid.name) == False:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Role name is not valid",
                )
                
                #create role
                role = Role(
                    name= valid.name,
                    organization = current_user.organization
                )
                session.add(role)
                session.commit()
                session.refresh(role)
                role_id = role.id
            else:
                role_id = role.id
        else:
            #create role
            if validate_name(valid.name) == False:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Role name is not valid",
            )
            role = Role(
                name=valid.name,
                organization = current_user.organization
            )
            session.add(role)
            session.commit()
            session.refresh(role)
            role_id = role.id

        # grant module permissions from list of modules defined as modules_togrant
        role_module_permission = session.exec(select(RoleModulePermission)
                                    .where((RoleModulePermission.role == role_id)&
                                          (RoleModulePermission.module == valid.module))).first()
        if(role_module_permission):
            role_module_permission.module = valid.module
            role_module_permission.access_policy = valid.policy
        else:
            role_module_permission= RoleModulePermission(
                    id=None,
                    role=role_id,
                    module= valid.module,
                    access_policy= valid.policy
                )

        session.add(role_module_permission)
        session.commit()
        session.refresh(role_module_permission)
        return {"id":role.id,"name": role.name}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    
@rr.put(endpoint['update'])
def update_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    valid: TemplateView,
):
    try:
        if not check_permission(
            session, "Update",role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        role = session.exec(select(Role).where(Role.id== valid.id)).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
      
        if validate_name(valid.name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name is not valid",
        )

        role.name = valid.name
        session.add(role)
        session.commit()
        session.refresh(role)
        print("module",valid.module,"policy")
        if (parse_enum(AccessPolicy,valid.policy, "policy") != None and parse_enum(mod,valid.module,"Module") != None):
            print("in here")
            role_module_permission = session.exec(select(RoleModulePermission)
                                    .where((RoleModulePermission.role == valid.id)&
                                          (RoleModulePermission.module == valid.module))).first()
            if(role_module_permission):
                role_module_permission.module = valid.module
                role_module_permission.access_policy = valid.policy
            else:
                role_module_permission= RoleModulePermission(
                        id=None,
                        role= valid.id,
                        module=valid.module,
                        access_policy=valid.policy
                    )

            session.add(role_module_permission)
            session.commit()
            session.refresh(role_module_permission)

    
        return {"id":role.id,"name": role.name}
       
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    
@rr.delete(endpoint['delete']+ "/{id}")
def delete_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int
) :
    try:
        # Check permission
        if not check_permission(
            session, "Delete",role_modules['delete'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        role = session.exec(select(db_model).where(db_model.id == id)).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        assigned_users = session.exec(select(User).where(User.role == id)).all()

        for user in assigned_users:
            user.role = None
            session.add(user)  # mark for update

        session.commit()

        assigned_role_module= session.exec(select(RoleModulePermission).where(RoleModulePermission.role == id)).all()

        for role_module in assigned_role_module:
            session.delete(role_module) 
            session.commit()   
        
        session.delete(role)
        session.commit()

        return {"message": f"user {endpoint_name} deleted successfully"}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
