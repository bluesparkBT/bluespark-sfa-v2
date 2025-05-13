from typing import Annotated, List, Dict, Any
from datetime import timedelta, date, datetime
from fastapi import APIRouter, HTTPException, Body, status, Depends, Path
from sqlmodel import select, Session
from db import get_session
from models.Account import User, ScopeGroup, ScopeGroupLink, Organization, Gender, Scope, Role, AccessPolicy
from utils.auth_util import verify_password, create_access_token, get_password_hash
from utils.util_functions import validate_name, validate_email, validate_phone_number
from utils.auth_util import get_tenant, get_current_user, check_permission, generate_random_password
from utils.model_converter_util import get_html_types
from utils.form_db_fetch import fetch_organization_id_and_name


AuthenticationRouter =ar= APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


@ar.post("/login/")
def login(
    session: SessionDep,
    tenant: str = Depends(get_tenant),
    
    username: str = Body(...),
    password: str = Body(...)
):
    
    try:
        user = session.exec(select(User).where(User.username == username)).first()
        print(user)
        
        if not user and not user.organization_id:
            raise HTTPException(status_code=400, detail="User missing company or organization info")

        if not user or not verify_password(password+user.username, user.hashedPassword):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        access_token_expires = timedelta(minutes=90)
        token = create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "organization": user.organization_id,
                },
            expires_delta = access_token_expires,
        )
        
        return {"access_token": token}
    
    except Exception as e:
        return {"error": str(e)}
 
@ar.get("/get-my-user/")
async def get_my_user(
    session: SessionDep,
    current_user: UserDep,
    user_id: int,   
     
    tenant: str = Depends(get_tenant),
):
    try:
        if not check_permission(
            session, "Read", "Users", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "id": user.id,
            "fullname": user.fullname,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "organization": user.organization_id,
            "role_id": user.role_id,
            "manager_id": user.manager_id,
            "scope": user.scope,
            "scope_group_id": user.scope_group_id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@ar.post("/create-superadmin/")
async def create_superadmin_user(
    session: SessionDep,
    tenant: str = Depends(get_tenant),  
    username: str = Body(...),
    email: str = Body(...),
    password: str = Body(...),
    service_provider_company: str = Body(...),
):
    try:
  
        existing_superadmin = session.exec(select(User).where(User.username== username)).first()
        if existing_superadmin is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Superadmin already registered",
            )
        
        organization = Organization(
            organization_name=service_provider_company,
        )

        session.add(organization)
        session.commit()
        session.refresh(organization)
        

        new_user =User(
            username=username,
            email=email,
            hashedPassword=get_password_hash(password + username),
            organization_id= organization.id,
        )
        
        
        session.add(new_user)
        session.commit()
        session.refresh(new_user)


        scope_group = ScopeGroup(
            scope_name="Superadmin scope",
        )
        
        session.add(scope_group)
        session.commit()
        session.refresh(scope_group)
        
        scope_group_link = ScopeGroupLink(
            scope_group_id=scope_group.id,
            organization_id=organization.id,
        )
        
        session.add(scope_group_link)
        session.commit()
        session.refresh(scope_group_link)

        # Link the scope group to the company (or organization)

        return {"message": "Superadmin created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@ar.delete("/delete-superadmin/")
async def delete_superadmin_user(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str = Depends(get_tenant),

    super_admin_id: int = Body(...),
):
    try:
        if not check_permission(
            session, "Delete", "Users", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        superadmin = session.exec(select(User).where(User.id == super_admin_id)).first()
        if not superadmin:
            raise HTTPException(status_code=404, detail="Superadmin not found")

        session.delete(superadmin)
        session.commit()

        return {"message": "Superadmin deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@ar.get("/get-users/")
async def get_users(
    session: SessionDep,
    current_user: UserDep,
    tenant: str = Depends(get_tenant),

):
    try:  
        if not check_permission(
            session, "Read", "Users", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        # users = session.exec(select(User)).all()
        # if not users:
        #     raise HTTPException(status_code=404, detail="No users found")
        # Fetch the ScopeGroup assigned to the current user
        user_scope_group = session.exec(
            select(ScopeGroup).where(ScopeGroup.id == current_user["scope_group_id"])
        ).first()
        if not user_scope_group:
            raise HTTPException(
                status_code=404, detail="ScopeGroup not found for the current user"
            )

        # Fetch the list of organizations associated with the ScopeGroup
        organization_ids = [
            org.id for org in user_scope_group.organizations
        ]
        if not organization_ids:
            raise HTTPException(
                status_code=404, detail="No organizations found for the user's ScopeGroup"
            )

        # Fetch users belonging to the organizations in the ScopeGroup
        users = session.exec(
            select(User).where(User.organization_id.in_(organization_ids))
        ).all()
        if not users:
            raise HTTPException(status_code=404, detail="No users found")
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "fullname": user.fullname,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "organization": user.organization_id,
                "role_id": user.role_id,
                "manager_id": user.manager_id,
                "scope": user.scope,
                "scope_group_id": user.scope_group_id,
            })
            
        return user_list

        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@ar.get("/user-form/")
async def create_user_form(
    session: SessionDep,
    current_user: User = Depends(get_current_user),    
    tenant: str = Depends(get_tenant),

):
    try:
        if not check_permission(
            session, "Read", "Users", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organizations = session.exec(select(Organization)).all()
        organization_list = [org.organization_name for org in organizations]

        roles = session.exec(select(Role)).all()
        role_list = [role.name for role in roles]
        
        scope_group = session.exec(select(ScopeGroup)).all()
        scope_group_list = [sg.scope_name for sg in scope_group]
        


        user_data = {
            "id": "", 
            "full_name": "", 
            "username": "",
            "email": "",
            "phone_number": "",
            "organization": fetch_organization_id_and_name(session),
            "role_id": role_list,
            "scope": {scope.value: scope.value for scope in Scope},
            "scope_group": scope_group_list,
            "gender": {gender.value: gender.value for gender in Gender},
        }

        return {"data": user_data, "html_types": get_html_types("users")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

      
@ar.post("/create-user/")
async def create_user(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str = Depends(get_tenant),

    fullname: str = Body(...),
    username: str = Body(...),
    raw_password: str = Body(...), 
    email: str = Body(...),
    role_id: int = Body(...),
    scope: Scope = Body(...),
    scope_group: int = Body(...),
    organization_id: int = Body(...),
    phone_number: str = Body(...),
    gender: Gender = Body(...),
            
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
        if validate_name(fullname) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fullname is not valid",
        )
        elif validate_email(email) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is not valid",
        )
        elif validate_phone_number(phone_number) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is not valid",
        )
            
        # Generate and hash password
        raw_password = generate_random_password()
        hashed_password = get_password_hash(raw_password + username)
        
        new_user = User(
            id= None,
            fullname=fullname,
            username=username,
            email=email,
            phone_number=phone_number,
            hashedPassword = hashed_password,
            organization_id= organization_id,
            role_id=role_id,           
            gender=gender,
            scope=scope,
            scope_group_id=scope_group,

        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return {
            "message": "User registered successfully",
            "temporary_password": raw_password }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@ar.get("/update-user-form/")
async def update_user_form(
    session: SessionDep,
    current_user: User = Depends(get_current_user),    
    tenant: str = Depends(get_tenant),

):
    try:
        if not check_permission(
            session, "Update", "Users", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organizations = session.exec(select(Organization)).all()
        organization_list = [org.organization_name for org in organizations]

        roles = session.exec(select(Role)).all()
        role_list = [role.name for role in roles]
        
        scope_group = session.exec(select(ScopeGroup)).all()
        scope_group_list = [sg.scope_name for sg in scope_group]
        

        scope = [s.value for s in Scope]
        gender = [g.value for g in Gender]

        user_data = {
            "id": "", 
            "full_name": "", 
            "username": "",
            "password": "",
            "email": "",
            "phone_number": "",
            "organization": organization_list,
            "role_id": role_list,
            "scope": scope,
            "scope_group": scope_group_list,
            "gender": gender,
            "position": "",
            "salary": "",
            "date_of_birth": "",
            "date_of_joining": "",
            "image": "file",
            "id_type": "",
            "id_number": "",
        }

        return {"data": user_data, "html_types": get_html_types("users")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@ar.put("/update-user/")
async def update_uer(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str = Depends(get_tenant),

    fullname: str = Body(...),
    username: str = Body(...),
    password: str = Body(...), 
    email: str = Body(...),
    role_id: int = Body(...),
    scope: Scope = Body(...),
    scope_group_id: str = Body(...),
    organization: int = Body(...),
    phone_number: str = Body(...),
    gender: Gender = Body(...),
    salary: float = Body(...),
    position: str = Body(...),
    date_of_birth: datetime = Body(...),
    date_of_joining: datetime = Body(...),
    id_type: str = Body(...),
    id_number: str = Body(...),
            
):
    try: 
        if not check_permission(
            session, "Update", "Users", current_user
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
        if validate_name(fullname) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fullname is not valid",
        )
        elif validate_email(email) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is not valid",
        )
        elif validate_phone_number(phone_number) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is not valid",
        )
        new_user = User(
            fullname=fullname,
            username=username,
            email=email,
            phone_number=phone_number,
            hashedPassword=get_password_hash(password + username),
            organization= organization,
            role_id=role_id,           
            gender=gender,
            salary=salary,
            position=position,
            date_of_birth=date_of_birth,
            date_of_joining=date_of_joining,
            id_type=id_type,
            id_number=id_number,
            scope=scope,
            scope_group_id=scope_group_id,

        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return {
            "message": "User: {new_user} registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@ar.delete("/delete-user/")
async def delete_user(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str = Depends(get_tenant),

    user_id: int = Body(...),
):
    try:
        if not check_permission(
            session, "Delete", "Users", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        session.delete(user)
        session.commit()

        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@ar.get("/scope-group-form/")
async def form_scope(
    session: SessionDep,
    current_user: User = Depends(get_current_user),    
    tenant: str = Depends(get_tenant),

):
    try:
        if not check_permission(
            session, "Read", "Administration", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organizations = session.exec(select(Organization)).all()

        organization_list = [
            org.organization_name
            for org in organizations
        ]
        
        data = {"id":"", 
                "name": ""
                }
        
        return {"data": data, "html_types": get_html_types("scope_group")}
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=400, detail=str(e))
    
@ar.post("/create-scope-group/")
async def create_scope_group(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str = Depends(get_tenant),

   scope_data: Dict[str, Any] = Body(...),
):
    try:
        if not check_permission(
            session, "Create", "Administration", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        scope_name = scope_data.get("name")

        if validate_name(scope_name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scope name is not valid",
        )

        

        existing_scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.scope_name == scope_name)).first()
        if existing_scope_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scope group already exists",
            )
      
        scope_group = ScopeGroup(
            scope_name=scope_name,
        )
        
        session.add(scope_group)
        session.commit()
        session.refresh(scope_group)

        return scope_group.id
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@ar.get("/scope-organization-form/")
async def form_scope_organization(
    session: SessionDep,
    current_user: UserDep,

):
    try:
        # if not check_accessPolicy(
        #     session, "edit", "Administration", current_user["user_id"]
        #     ):
        #     raise HTTPException(
        #         status_code=403, detail="You Do not have the required privilege"
        #     )
        
        org = {"scope_id":"", 
                "organizations": fetch_organization_id_and_name(session)
                }
        print(org)
        
        return {"data": org, "html_types": get_html_types("scope_organization")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
@ar.post("/add-scope-organization/")
async def add_organization_to_scope(
    session: SessionDep,
    current_user: UserDep,
    scope_id:int = Body(...),
    organizations: List[int] = Body(...)
):
    try:
        # if not check_accessPolicy(
        #     session, "edit", "Administration", current_user["user_id"]
        #     ):
        #     raise HTTPException(
        #         status_code=403, detail="You Do not have the required privilege"
        #     )
      

        scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == scope_id)).first()
        if not scope_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scope group not found",
            )
        
        existing_orgs = [organization.id for organization in scope_group.organizations ]
        print(existing_orgs)
    
        existing_org_ids = set(existing_orgs)
        new_org_ids_set = set(organizations)

        # Add new entries
        to_add = new_org_ids_set - existing_org_ids
        for org_id in to_add:
            scope_group_link_add = ScopeGroupLink(scope_group_id=scope_id, organization_id=org_id)
            session.add(scope_group_link_add)
            session.commit()
            session.refresh(scope_group_link_add)


      # Remove obsolete entries
        to_remove = existing_org_ids - new_org_ids_set
        if to_remove:
            scope_group_link_remove = session.exec(select(ScopeGroupLink)
                .where(ScopeGroupLink.scope_group_id == scope_id)
                .where(ScopeGroupLink.organization_id.in_(to_remove))).first()
            session.delete(scope_group_link_remove)
            session.commit()
            

        return "Organization in Scope Group updated successfully"
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    


@ar.get("/get-scope-groups/")
async def get_scope_groups(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str = Depends(get_tenant),

):
    try:
        if not check_permission(
            session, "Read", "Administration", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        scope_groups = session.exec(select(ScopeGroup)).all()
        if not scope_groups:
            raise HTTPException(status_code=404, detail="No scope groups found")
        
        scope_group_list = []
        
        for scope_group in scope_groups:
            scope_group_list.append({
                "id": scope_group.id,
                "scope_name": scope_group.scope_name,
                "organizations": [org.organization_name for org in scope_group.organizations],
            })
            
        return scope_group_list

        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@ar.get("/get-scope-group/{id}")
async def get_scope_group(
    session: SessionDep,
    current_user: UserDep,
    id: int
):
    try:
        # if not check_accessPolicy(
        #     session, "edit", "Administration", current_user["user_id"]
        #     ):
        #     raise HTTPException(
        #         status_code=403, detail="You Do not have the required privilege"
        #     )
        scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == id)).first()
        if not scope_group:
            raise HTTPException(status_code=404, detail="Scope Group not found")
   
       
            
        return {
                "id": scope_group.id,
                "name": scope_group.scope_name,
                "organizations": [org.id for org in scope_group.organizations],
            }

        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    


@ar.put("/update-scope-group/")
async def update_scope_group(
    session: SessionDep,
    current_user: UserDep,    
    tenant: str = Depends(get_tenant),

    name: str = Body(...) ,
    id: int = Body(...),
):
    try:
        if not check_permission(
            session, "Delete", "Administration", current_user
            ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name is not valid",
        )

        scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == id)).first()
        if not scope_group:
            raise HTTPException(status_code=404, detail="Role not found")
      
        if validate_name(name) == False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name is not valid",
        )

        scope_group.scope_name = name
        session.add(scope_group)
        session.commit()
        session.refresh(scope_group)


        return scope_group.id
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@ar.delete("/delete-scope-group/{id}")
async def delete_scope_group(
    session: SessionDep,
    id: int,
    current_user: User = Depends(get_current_user),
):
    try:
        # if not check_accessPolicy(
        #     session, "edit", "Administration", current_user["user_id"]
        #     ):
        #     raise HTTPException(
        #         status_code=403, detail="You Do not have the required privilege"
        #     )
        scope_group_links = session.exec(select(ScopeGroupLink).where(ScopeGroupLink.scope_group_id == id)).all()
        if scope_group_links:
            for scope_group_link in scope_group_links:
                session.delete(scope_group_link)
                session.commit()

        scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == id)).first()
        if not scope_group:
            raise HTTPException(status_code=404, detail="Scope group not found")

        session.delete(scope_group)
        session.commit()

        return {"message": "Scope group deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

