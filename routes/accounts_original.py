import traceback
from typing import Annotated, List, Dict, Any, Optional
from datetime import timedelta, date, datetime
from fastapi import APIRouter, HTTPException, Body, status, Depends, Path
from sqlmodel import select, Session
from db import get_session
from models.Account import User, ScopeGroup, ScopeGroupLink, Organization, Gender, Scope, Role, AccessPolicy, IdType
from utils.auth_util import verify_password, create_access_token, get_password_hash
from utils.util_functions import validate_name, validate_email, validate_phone_number, parse_datetime_field, format_date_for_input, parse_enum
from utils.auth_util import get_current_user, check_permission, generate_random_password, add_organization_path, extract_username
from utils.model_converter_util import get_html_types
from utils.get_hierarchy import get_child_organization, get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_organization_id_and_name, fetch_role_id_and_name, fetch_scope_group_id_and_name, fetch_address_id_and_name
import traceback

Domain= "http://172.10.10.203:5000"
ACCESS_TOKEN_EXPIRE_DAYS = 2

AuthenticationRouter =ar= APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


@ar.post("/login/")
def login(
    session: SessionDep,
    tenant: str,
    
    username: str = Body(...),
    password: str = Body(...)
):
    try:
        current_tenant = session.exec(select(Organization).where(Organization.tenant_hashed == tenant)).first()
        if not current_tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        db_username = add_organization_path(username, current_tenant.name)
        user = session.exec(
            select(User).where(User.username == db_username)
        ).first()
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
    
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}
 
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
            print("super admin user:", superadmin_user)

            username_display = extract_username(superadmin_user.username, service_provider.name)
            name = service_provider.name
        else:
            current_tenant = session.exec(
                select(Organization).where(Organization.tenant_hashed == tenant)
            ).first()
            if not current_tenant:
                raise HTTPException(status_code=404, detail="Tenant not found")

            name = current_tenant.name
            username_display = extract_username(user.username, name)

        return {
            "id": user.id,
            "full_name": user.full_name,
            "username": username_display,
            "phone_number": user.phone_number,
            "organization": name,
            "role": user.role,
            "manager_id": user.manager_id,
            "scope": user.scope,
            "scope_group": user.scope_group,
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@ar.get("/get-users")
async def get_users(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
):
    try:  
        if not check_permission(
            session, "Read", ["Administrative", "Users"], current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        users = session.exec(
            select(User).where(User.organization.in_(organization_ids))
        ).all()

        user_list = []
        for user in users:
            # Fetch the organization for each user
            user_org = session.exec(
                select(Organization).where(Organization.id == user.organization)
            ).first()

            if not user_org:
                continue  

            # Extract username without tenant prefix
            username_display = extract_username(user.username, user_org.name)
            user_scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == user.scope_group)).first()
            if user_scope_group:
                scope_group = user_scope_group.name
            user_role = session.exec(select(Role).where(Role.id == user.role)).first()
            manager = session.exec(select(User).where(User.id == user.manager_id)).first()
            user_list.append({
                "id": user.id,
                "full_name": user.full_name,
                "username": username_display,
                "email": user.email,
                "phone_number": user.phone_number,
                "organization": user_org.name,
                "role": user_role.name,
                "manager": manager,
                "scope": user.scope,
                "scope_group": scope_group,
            })

        return user_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

    
@ar.get("/get-user/{id}")
async def get_user(
    session: SessionDep,
    id: int,
    tenant: str,
    current_user: UserDep,
):
    try:
        if not check_permission(
            session, "Read", "Users", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        user = session.exec(select(User).where(User.id == id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = {
            "id": user.id, 
            "full_name": user.full_name, 
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "organization": user.organization,
            "role": user.role,
            "scope": user.scope,
            "scope_group": user.scope_group,
            "gender": user.gender,
            "date_of_birth": format_date_for_input(user.date_of_birth),
            "date_of_joining": format_date_for_input(user.date_of_joining),
            "salary": 0 if user.salary is None else user.salary,
            "position":user.position,
            "image": user.image,
            "id_type": user.id_type,
            "id_number": user.id_number,
            "password": "",
        }
       
        return user_data
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@ar.get("/user-form/")
async def create_user_form(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,    

):
    try:
        if not check_permission(
            session, "Read", "Users", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        user = session.exec(select(User).where(User.id == current_user.id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # current_tenant = session.exec(
        #     select(Organization).where(Organization.tenant_hashed == tenant)
        # ).first()

        user_data = {
            "id": "", 
            "full_name": "", 
            "username": "",
            "email": "",
            "phone_number": "",
            "organization": fetch_organization_id_and_name(session, current_user),
            "role": fetch_role_id_and_name(session, current_user),
            "scope": {scope.value: scope.value for scope in Scope},
            "scope_group": fetch_scope_group_id_and_name(session, current_user),
            "gender": {gender.value: gender.value for gender in Gender},
            "address": fetch_address_id_and_name(session, current_user)
        }

        return {"data": user_data, "html_types": get_html_types("user")}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
   
@ar.post("/create-user/")
async def create_user(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str,

    full_name: str = Body(...),
    username: str = Body(...),
    email: str | None = Body(...),
    role: int = Body(...),
    scope: str = Body(...),
    scope_group: int = Body(...),
    organization: int = Body(...),
    phone_number:Optional [str | None] = Body(None),
    gender: Optional[str] = Body(None),
    address : Optional[int| str| None] = Body(default=None),
            
):
    try: 
        if not check_permission(
            session, "Create", "Users", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        existing_user = session.exec(select(User).where(User.username == username)).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
        #check input validity
        if validate_name(full_name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="full_name is not valid",
        )
        elif email is not None and validate_email(email) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is not valid",
        )
        elif phone_number is not None and validate_phone_number(phone_number) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is not valid",
        )
        
        if address == "" or address is None:
            address = None
            
        current_tenant = session.exec(select(Organization).where(Organization.id == current_user.organization)).first() if tenant == "provider" else session.exec(select(Organization).where(Organization.tenant_hashed == tenant)).first()
        print("the organization get from", current_tenant)   
               
        user_name = username
        stored_username = add_organization_path(user_name, current_tenant.name)

        password = generate_random_password()
        hashed_password = get_password_hash(password + stored_username)
        
        new_user = User(
            id= None,
            full_name=full_name,
            username= stored_username,
            email=email,
            phone_number=phone_number,
            hashedPassword = hashed_password,
            organization= organization,   
            role= role,       
            gender=parse_enum(Gender,gender, "Gender"),
            scope=parse_enum(Scope,scope, "Scope"),
            scope_group=scope_group,
            address_id = address

        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)


        return {
            "message": "User registered successfully",
            "domain" : f"{Domain}/signin" if tenant == "provider" else f"{Domain}/{tenant}/signin",
            "username": user_name,
            "password": password }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@ar.get("/update-user-form/")
async def update_user_form(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,    

):
    try:
        if not check_permission(
            session, "Update", "Users", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
     

        user_data = {
            "id": "", 
            "full_name": "", 
            "username": "",
            "email": "",
            "phone_number": "",
            "organization": fetch_organization_id_and_name(session, current_user),
            "role": fetch_role_id_and_name(session, current_user),
            "scope": {scope.value: scope.value for scope in Scope},
            "scope_group": fetch_scope_group_id_and_name(session, current_user),
            "gender": {gender.value: gender.value for gender in Gender},
            "date_of_birth": "",
            "date_of_joining": "",
            "salary": 0,
            "position": "",
            "image": "",
            "id_type": {i.value: i.value for i in IdType},
            "id_number": "",
            "password": "",
            "address": fetch_address_id_and_name(session, current_user)


        }

        return {"data": user_data, "html_types": get_html_types("user")}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@ar.put("/update-user/")
async def update_user(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str,
    id: int = Body(...),
    full_name: str = Body(...),
    username: str = Body(...),
    email: Optional[str | None] = Body(...),
    role: int = Body(...),
    scope: str = Body(...),
    scope_group: int = Body(...),
    organization: int = Body(...),
    phone_number: Optional[str| None] = Body(None),
    gender: Optional[str] = Body(None),
    salary: float = Body(...),
    position: str = Body(...),
    date_of_birth:  Optional[str]  = Body(...),
    date_of_joining:  Optional[str]  = Body(...),
    id_type: str = Body(...),
    id_number: str = Body(...),
    image: str = Body(...),    
    address: Optional[int |str | None] = Body(...)      
            
):
    try: 
        if not check_permission(
            session, "Update", "Users", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        existing_user = session.exec(select(User).where(User.id == id)).first()
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not exist",
            )
        # Check input validity
        if not validate_name(full_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="full_name is not valid",
            )
        elif email is not None and validate_email(email) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is not valid",
        )
        elif phone_number is not None and validate_phone_number(phone_number) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is not valid",
        )
            
        if address == "" or address is None:
            address = None

       
        existing_user.full_name = full_name
        existing_user.username = username
        existing_user.email = email
        existing_user.phone_number = phone_number
        # existing_user.hashedPassword = get_password_hash(password + username) if password != "" else existing_user.hashedPassword
        existing_user.organization = organization
        existing_user.gender = parse_enum(Gender,gender, "Gender")
        existing_user.salary = float(salary)
        existing_user.position = position
        existing_user.date_of_birth = parse_datetime_field(date_of_birth)
        existing_user.date_of_joining = parse_datetime_field(date_of_joining)
        existing_user.id_type = parse_enum(IdType,id_type, "Id Type")
        existing_user.id_number = id_number
        existing_user.scope = parse_enum(Scope,scope, "Scope")
        existing_user.scope_group = scope_group
        existing_user.image = image
        existing_user.role = role
        existing_user.address_id = address

        session.add(existing_user)
        session.commit()
        session.refresh(existing_user)


        return {
            "message": "User updated successfully"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
      
@ar.delete("/delete-user/{id}/")
async def delete_user(
    session: SessionDep,
    current_user: UserDep,
    id: int
):
    try:
        if not check_permission(session, "Delete", "Users", current_user):
            raise HTTPException(status_code=403, detail="You do not have the required privilege")

        user = session.get(User, id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        session.delete(user)
        session.commit()

        return {"message": "User deleted successfully"}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@ar.get("/get-scope-groups/")
async def get_scope_groups(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str,

):
    try:
        if not check_permission(
            session, "Read", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        filtered_scope_groups = fetch_scope_group_id_and_name(session, current_user)
        print("fetched scope groups::::", filtered_scope_groups)

        filtered_scope_group_ids = list(filtered_scope_groups.keys())
        scope_groups = session.exec(
            select(ScopeGroup)
            .where(ScopeGroup.id.in_(filtered_scope_group_ids))
            .distinct()
        ).all()

        
        if not scope_groups:
            raise HTTPException(status_code=404, detail="No scope groups found for your organization")
        
        scope_group_list = []
        for scope_group in scope_groups:
            scope_group_list.append({
                "id": scope_group.id,
                "name": scope_group.name,
                "organizations": [org.name for org in scope_group.organizations],
            })

        return scope_group_list

        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
   
 
@ar.get("/get-scope-group/{id}")
async def get_scope_group(
    session: SessionDep,
    current_user: UserDep,
    id: int
):
    try:
        if not check_permission(
            session, "Read", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == id)).first()
        if not scope_group:
            raise HTTPException(status_code=404, detail="Scope Group not found")
   
       
            
        return {
                "id": scope_group.id,
                "name": scope_group.name,
                "hidden": [org.id for org in scope_group.organizations],
            }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@ar.get("/scope-group-form/")
async def form_scope_organization(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        if not check_permission(
            session, "Read", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        current_tenant = session.exec(select(Organization).where(Organization.id == current_user.organization)).first() if tenant == "provider" else session.exec(select(Organization).where(Organization.tenant_hashed == tenant)).first()
       
        print("current tenant",get_child_organization(session, current_user.organization) )
        
        org = {
               "id": "",
               "name":"", 
               "hidden": [get_child_organization(session, current_user.organization)]
            }
                    
        return {"data": org, "html_types": get_html_types("scope_group")}
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@ar.post("/create-scope-group/")
async def add_organization_to_scope(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    name: str = Body(...),
    hidden: List[int] = Body(...),
):
    try:
        if not check_permission(
            session, "Create", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        if validate_name(name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scope name is not valid",
        )

        existing_scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.name == name)).first()
        
        if existing_scope_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scope group already exists",
            )
        scope_group = ScopeGroup(
            name=name,
            parent_id = current_user.organization
        )
        
        session.add(scope_group)
        session.commit()
        session.refresh(scope_group)
     
        #Add new entries
        to_add = set(hidden)
        for org_id in to_add:
            scope_group_link_add = ScopeGroupLink(
                scope_group=scope_group.id,
                organization=org_id
                )
            session.add(scope_group_link_add)
            session.commit()
            session.refresh(scope_group_link_add)
           

        return "Organization in Scope Group updated successfully"
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    

@ar.put("/update-scope-group/")
async def update_scope_group(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str,
    id: int = Body(...),
    name: str = Body(...) ,
    hidden: List[int] = Body(...)
):
    try:
        if not check_permission(
            session, "Update", "Administrative", current_user
            ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You Do not have the required privilege",
        )

        scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == id)).first()
        if not scope_group:
            raise HTTPException(status_code=404, detail="Role not found")
        
      
        if validate_name(name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scope group name is not valid",
        )
        
        scope_group.name = name
        session.add(scope_group)
        session.commit()
        session.refresh(scope_group)
        
        existing_orgs = [organization.id for organization in scope_group.organizations ]
        existing_org_ids = set(existing_orgs)
        new_org_ids_set = set(hidden)
        print("existing", existing_org_ids)
        print("new", new_org_ids_set)
        # Add new entries
        to_add = new_org_ids_set - existing_org_ids
        for org_id in to_add:
            scope_group_link_add = ScopeGroupLink(scope_group=id, organization=org_id)
            session.add(scope_group_link_add)
            session.commit()
            session.refresh(scope_group_link_add)


      # Remove obsolete entries
        to_remove = existing_org_ids - new_org_ids_set
        if to_remove:
            links_to_remove = session.exec(
                select(ScopeGroupLink)
                .where(ScopeGroupLink.scope_group == id)
                .where(ScopeGroupLink.organization.in_(to_remove))
            ).all()

            for link in links_to_remove:
                session.delete(link)
                session.commit()

        return scope_group.id
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@ar.delete("/delete-scope-group/{id}")
async def delete_scope_group(
    session: SessionDep,
    id: int,
    current_user: UserDep,
):
    try:
        # Permission check
        if not check_permission(session, "Delete", "Administrative", current_user):
            raise HTTPException(status_code=403, detail="You do not have the required privilege")

        # Ensure scope group exists before proceeding
        scope_group = session.get(ScopeGroup, id)
        if not scope_group:
            raise HTTPException(status_code=404, detail="Scope group not found")

        # Delete links associated with the scope group
        scope_group_links = session.exec(select(ScopeGroupLink).where(ScopeGroupLink.scope_group == id)).all()
        for link in scope_group_links:
            session.delete(link)

        # Unassign users from the scope group
        assigned_users = session.exec(select(User).where(User.scope_group == id)).all()
        for user in assigned_users:
            user.scope_group = None
            session.add(user)  # mark for update

        # Delete the scope group
        session.delete(scope_group)

        # Commit all changes at once
        session.commit()
        
        session.refresh()

        return {"message": "Scope group deleted successfully"}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
