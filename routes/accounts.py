from typing import Annotated, List, Dict, Any, Optional, Union
from datetime import timedelta
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from utils.model_converter_util import get_html_types
from models.Account import User, ScopeGroup,ScopeGroupLink 
from utils.util_functions import validate_name
from models.viewModel.AccountsView import UserAccountView as TemplateView, UpdateUserAccountView as UpdateTemplateView
from models.Account import User, ScopeGroup, ScopeGroupLink, Organization, Gender, Scope, Role, AccessPolicy, IdType
from utils.util_functions import validate_name, validate_email, validate_phone_number, parse_datetime_field, format_date_for_input, parse_enum
from utils.auth_util import get_current_user, check_permission, check_permission_and_scope, add_organization_path, verify_password, get_password_hash, create_access_token, generate_random_password, extract_username
import copy
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_user_id_and_name, fetch_organization_id_and_name, fetch_role_id_and_name, fetch_scope_group_id_and_name, fetch_address_id_and_name
import traceback

Domain= "http://172.10.10.203:3000"
ACCESS_TOKEN_EXPIRE_DAYS = 2

AccountRouter = ar = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "account"
db_model = User

endpoint = {
    "get": f"/get-{endpoint_name}s",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",
    "update": f"/update-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}
role_modules = {   
    "read": ["Administrative"],
    "get_form": ["Administrative"],
    "create": ["Service Provider", "Administrative"],
    "update": ["Administrative", "Service Provider"],
    "delete": ["Administrative"],
}

#Authentication Related
@ar.post("/login/")
def login(
    session: SessionDep,
    tenant: str,
    username: str = Body(...),
    password: str = Body(...)
):
    try:
        current_tenant = session.exec(select(Organization).where(Organization.tenant_hashed == tenant)).first()
        print("current tenant found", current_tenant)
        if not current_tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        db_username = add_organization_path(username, current_tenant.name)
    
        user = session.exec(
            select(User).where(User.username == db_username)
        ).first()
        print("user found", user)
        print(password, db_username, user.hashedPassword)

        if not user or not verify_password(password + db_username, user.hashedPassword):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
        access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        token = create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "organization": user.organization,
                },
            expires_delta = access_token_expires,
        )
        
        return {"access_token": token}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

@ar.get("/get-my-user/")
async def get_my_user(
    session: SessionDep,
    current_user: UserDep,
    tenant: Optional[str] = None,  # Make tenant optional
):
    try:
        user = session.exec(select(User).where(User.id == current_user.id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not tenant or tenant.lower() == "provider":
            service_provider = session.exec(select(Organization).where(Organization.organization_type == "Service Provider")).first()
            superadmin_user = session.exec(select(User).where(User.id == current_user.id)).first()

            username_display = extract_username(superadmin_user.username, service_provider.name)
            tenant_name = service_provider.name
        else:
            current_tenant = session.exec(
                select(Organization).where(Organization.tenant_hashed == tenant)
            ).first()
            if not current_tenant:
                raise HTTPException(status_code=404, detail="Tenant not found")

            tenant_name = current_tenant.name
            username_display = extract_username(user.username, tenant_name)

        return {
            "id": user.id,
            "full_name": user.full_name,
            "username": username_display,
            "phone_number": user.phone_number,
            "organization": tenant_name,
            "role": user.role,
            "manager": user.manager,
            "scope": user.scope,
            "scope_group": user.scope_group,
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    
@ar.get(endpoint['get'])
def get_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str

):
    try:  
        if not check_permission(
            session, "Update", role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        if tenant == "provider":
            current_tenant = session.exec(select(Organization).where(Organization.id == current_user.organization)).first()   
        else :
            current_tenant = session.exec(select(Organization).where(Organization.tenant_hashed == tenant)).first()
        
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        entries_list = session.exec(
            select(db_model).where(db_model.organization.in_(organization_ids), db_model.organization == current_tenant.id)
        ).all()
        
        if not entries_list:
            raise HTTPException(status_code=404, detail="No User found")
        

        user_list = []
        for user in entries_list:
            # Fetch the organization for each user
            user_org = session.exec(
                select(Organization).where(Organization.id == user.organization)
            ).first()

            if not user_org:
                continue  

            # Extract username without tenant prefix
            username_display = extract_username(user.username, current_tenant.name)
            user_scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == user.scope_group)).first()
            print("scope group found::", user_scope_group)
            if user_scope_group:
                scope_group = user_scope_group.name
            user_role = session.exec(select(Role.name).where(Role.id == user.role)).first()
            if not user_role:
                user_role = "N/A"
            manager = session.exec(select(User).where(User.id == user.manager)).first()
            if not manager:
                manager = "N/A"
            user_list.append({
                "id": user.id,
                "full_name": user.full_name,
                "username": username_display,
                "email": user.email,
                "phone_number": user.phone_number,
                "organization": user_org.name,
                "role": user_role,
                "manager": manager,
                "scope": user.scope,
                "scope_group": scope_group,
            })

        return user_list

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

@ar.get(endpoint['get_by_id'] + "/{id}")
def get_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int,
):
    try:
        if not check_permission(
            session, "Read", role_modules['read'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        entry = session.exec(
            select(db_model).where(db_model.organization.in_(organization_ids), db_model.id == id)
        ).first()  
        print("is entry found::", entry)
        if not entry:
            raise HTTPException(status_code=404, detail="User not found")
              
        if not tenant or tenant.lower() == "provider":
            service_provider = session.exec(select(Organization).where(Organization.organization_type == "Service Provider")).first()
            tenant_name = service_provider.name
        else:
            current_tenant = session.exec(
                select(Organization).where(Organization.tenant_hashed == tenant)
            ).first()
            if not current_tenant:
                raise HTTPException(status_code=404, detail="Tenant not found")

            tenant_name = current_tenant.name
            
        data =  {
            "id": entry.id,
            "full_name": entry.full_name,
            "username": extract_username(entry.username, tenant_name),
            "email": entry.email,
            "phone_number": entry.phone_number,
            "role": entry.role,
            "scope": entry.scope,
            "scope_group": entry.scope_group,
            "organization": entry.organization,
            "gender": entry.gender,
            "address": entry.address,
            "manager": entry.manager,

        }
        
        if tenant == "provider":
            del data['organization']
            del data['scope']
            del data['manager']
        
        return data
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    
@ar.get(endpoint['get_form'])
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
        form_structure = {
            "id": "", 
            "full_name": "", 
            "username": "",
            "email": "",
            "phone_number": "",
            "role": fetch_role_id_and_name(session, current_user),
            "scope": {i.value: i.value for i in Scope},
            "scope_group": fetch_scope_group_id_and_name(session, current_user),
            "organization": fetch_organization_id_and_name(session, current_user),
            "gender": {i.value: i.value for i in Gender},
            # "salary": 0,
            # "position": "",            
            # "date_of_birth": "",
            # "date_of_joining": "",
            # "image": "",
            # "id_type": {i.value: i.value for i in IdType},
            # "id_number": "",
            "address": fetch_address_id_and_name(session, current_user)

        } 
        
        html_types = copy.deepcopy(get_html_types("user"))
        if tenant == "provider":
          
            del html_types['organization']
            del html_types['scope']
            del html_types['manager']
            del form_structure['organization']

        return {"data": form_structure, "html_types": html_types}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

@ar.post(endpoint['create'])
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
        if tenant == "provider":
            current_tenant = session.exec(select(Organization).where(Organization.id == current_user.organization)).first()
            
        else :
            current_tenant = session.exec(select(Organization).where(Organization.tenant_hashed == tenant)).first()
                    
        user_name = valid.username
        stored_username = add_organization_path(user_name, current_tenant.name)
        password = generate_random_password()
        hashed_password = get_password_hash(password + stored_username)
        
        new_user = User(
            id= None,
            full_name=valid.full_name,
            username= stored_username,
            email=valid.email,
            phone_number=valid.phone_number,
            organization= current_user.organization if tenant == "provider" else valid.organization,   
            role= valid.role, 
            scope=Scope.personal_scope,
            scope_group=valid.scope_group,                  
            gender=parse_enum(Gender,valid.gender, "Gender"),
            manager = None if tenant == "provider" else valid.organization,   
            address = valid.address,
            hashedPassword = hashed_password,

        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)


        return {
            "message": "User registered successfully",
            "domain" : f"{Domain}/signin" if tenant == "provider" else f"{Domain}/{tenant}/signin",
            "username": user_name,
            "password": password }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
 
    
@ar.put(endpoint['update'])
def update_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    valid: UpdateTemplateView,
):
    try:
        # Check permission
        if not check_permission(
            session, "Update",role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        selected_entry = session.exec(
            select(db_model).where(db_model.organization.in_(organization_ids), db_model.id == valid.id)
        ).first()
        user_org = session.exec(select(Organization).where(Organization.id == selected_entry.organization)).first() 
        old_username = selected_entry.username
        new_username = add_organization_path(valid.username, user_org.name)
        
        selected_entry.full_name = valid.full_name
        selected_entry.username = new_username
        selected_entry.email = valid.email
        selected_entry.phone_number = valid.phone_number
        selected_entry.organization = current_user.organization if tenant == "provider" else valid.organization
        # if verify_password(valid.old_password + old_username, selected_entry.hashedPassword):
        #     selected_entry.hashedPassword = get_password_hash(valid.password + selected_entry.username)
        # else:
        #     raise HTTPException(status_code=401, detail="Incorrect password")
        if valid.gender:
            selected_entry.gender = parse_enum(Gender, valid.gender, "Gender")
        # if valid.salary is not None:
        #     selected_entry.salary = float(valid.salary)
        # if valid.position:
        #     selected_entry.position = valid.position
        # if valid.date_of_birth:
        #     selected_entry.date_of_birth = parse_datetime_field(valid.date_of_birth)
        # if valid.date_of_joining:
        #     selected_entry.date_of_joining = parse_datetime_field(valid.date_of_joining)
        # if valid.id_type:
        #     selected_entry.id_type = parse_enum(IdType, valid.id_type, "Id Type")
        # if valid.id_number:
        #     selected_entry.id_number = valid.id_number
        if valid.scope and tenant != "provider":
            selected_entry.scope = parse_enum(Scope, valid.scope, "Scope")
        if valid.scope_group:
            selected_entry.scope_group = valid.scope_group
        # if valid.image:
        #     selected_entry.image = valid.image
        if valid.role:
            selected_entry.role = valid.role
        if valid.address:
            selected_entry.address = valid.address
 
        session.add(selected_entry)
        session.commit()
        session.refresh(selected_entry)

        return {
            "message": "User registered successfully",
            "domain" : f"{Domain}/signin" if tenant == "provider" else f"{Domain}/{tenant}/signin",
            "username": selected_entry.username,
            # "password": "password not changed" if valid.password == None else valid.password
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Something went wrong")

@ar.delete(endpoint['delete']+ "/{id}")
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
        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        selected_entry = session.exec(
            select(db_model).where(db_model.organization.in_(organization_ids), db_model.id == id)
        ).first()

        if not selected_entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

    
        # Delete category after validation
        session.delete(selected_entry)
        session.commit()

        return {"message": f"user {endpoint_name} deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Something went wrong")
