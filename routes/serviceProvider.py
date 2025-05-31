
from typing import Annotated, List, Dict, Any
from datetime import timedelta, date, datetime
from fastapi import APIRouter, HTTPException, Body, status, Depends, Path
from sqlmodel import select, Session
from db import get_session
import traceback
from utils.auth_util import verify_password, create_access_token, get_password_hash
from utils.util_functions import validate_name, validate_email, validate_phone_number, parse_enum
from utils.auth_util import get_current_user, check_permission, generate_random_password, get_tenant_hash, extract_username, add_organization_path

from utils.model_converter_util import get_html_types
from utils.form_db_fetch import get_organization_ids_by_scope_group
from utils.domain_util import getPath
from utils.auth_util import check_permission_and_scope

from models.Account import User, ScopeGroup, ScopeGroupLink, Organization, OrganizationType, RoleModulePermission, Scope, Role, AccessPolicy
from models.Account import ModuleName as modules
from models.viewModel.AccountsView import SuperAdminView as TemplateView
from models.viewModel.AccountsView import OrganizationView, UpdateSuperAdminView

endpoint_name = "superadmin"

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
    "get": ["Service Provider", "Tenant Management"],
    "get_form": ["Service Provider", "Tenant Management"],
    "create": ["Service Provider", "Tenant Management"],
    "update": ["Service Provider", "Tenant Management"],
    "delete": ["Service Provider"],
}

# frontend domain
Domain= getPath()

service_provider_company = "Bluespark"
ACCESS_TOKEN_EXPIRE_DAYS = 2

ServiceProvider = c = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


#Authentication Related
@c.get("/has-superadmin")
def has_superadmin_created(
    session: SessionDep
) -> bool:
    # Find a user whose role is named "Super Admin"
    role = session.exec(select(Role).where(Role.name == "Super Admin")).first()
    if not role:
        return False
    superadmin = session.exec(select(User).where(User.role == role.id)).first()
    # superadmin = session.exec(
    #     select(User)
    #     .join(Role, User.role == Role.id)
    #     .where(Role.name == "Super Admin")
    # ).first()
    if superadmin:
        print("Super admin exists")
        return True
    else:
        print("No super admin found")
        return False

@c.post("/login/")
def login(
    session: SessionDep,
    
    username: str = Body(...),
    password: str = Body(...)
):
    try:
        service_provider = session.exec(select(Organization).where(Organization.organization_type == OrganizationType.service_provider)).first()
        db_username = add_organization_path(username, service_provider.name)

        user = session.exec(select(db_model).where(db_model.username == db_username)).first()
        if not user:
            raise HTTPException(status_code=400, detail="User Not Found")

        print("this are the credentials:", password, db_username, user.hashedPassword)
        if not user or not verify_password(password+db_username, user.hashedPassword):
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
#CRUD
@c.get(endpoint['get'])
def get(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        orgs_in_scope = check_permission_and_scope(session, "Read", role_modules['get'], current_user)

        entries_list = session.exec(
            select(db_model).where(db_model.organization.in_(orgs_in_scope["organization_ids"]))
        ).all()

        return entries_list

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
 
@c.get(endpoint['get_by_id'] + "/{id}")
def get_by_Id_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int,
):
    try:

        orgs_in_scope = check_permission_and_scope(session, "Update", role_modules['update'], current_user)
        entry = session.exec(
            select(db_model).where(db_model.organization.in_(orgs_in_scope["organization_ids"]), db_model.id == id)
        ).first()

        if not entry:
            raise HTTPException(status_code=404, detail="Category not found")
        

        return entry
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    
@c.post(endpoint['create'])
def create_template(
    session: SessionDep,
    valid: TemplateView,
):
    try:
        existing_superadmin = session.exec(select(User).where(User.role == Role.id == "Super Admin")).first()

        if existing_superadmin is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Superadmin already registered",
            )

        #create new service provider and super admin            
        service_provider = Organization(
            name="Blue Spark Business Technology",
            owner_name= "Mekonen",
            organization_type=OrganizationType.service_provider,
            description="Service Provider and owner of this Sales Force Automation system",
        )
        session.add(service_provider)
        session.commit()
        session.refresh(service_provider)

        # Check if Super Admin Scope group exists
        existing_scope_group = session.exec(
            select(ScopeGroup).where(ScopeGroup.name == "Super Admin Scope")
        ).first()
        if existing_scope_group:
            service_provider_scope_group = existing_scope_group
        else:
            service_provider_scope_group = ScopeGroup(
                name="Super Admin Scope",
                tenant_id = service_provider.id
                    )
            session.add(service_provider_scope_group)
            session.commit()
            session.refresh(service_provider_scope_group)

        scope_group_link = ScopeGroupLink(
            scope_group=service_provider_scope_group.id,
            organization=service_provider.id,

        )
        session.add(scope_group_link)
        session.commit()
        session.refresh(scope_group_link)
        
        #create role
        role = Role(
            name="Super Admin",
            organization = service_provider.id

        )
        session.add(role)
        session.commit()
        session.refresh(role)

        # List of modules the Super Admin should have access to
        modules_to_grant = [
            modules.service_provider.value,
            modules.administrative.value,
            modules.tenant_management.value,
        ]
        for module in modules_to_grant: 
            role_module_permission= RoleModulePermission(
                role=role.id,
                module=module,
                access_policy=AccessPolicy.manage
            )
            session.add(role_module_permission)
        session.commit()
        
        stored_username = add_organization_path(valid.username, service_provider.name)
        new_user = User(
            full_name=valid.full_name,
            username=stored_username,
            email=valid.email,
            hashedPassword=get_password_hash(valid.password + stored_username),
            organization=service_provider.id,
            role=role.id,
            scope = Scope.managerial_scope.value,
            scope_group=service_provider_scope_group.id,

        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return {"message": "Superadmin created successfully"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
 
@c.post(endpoint['update'])
def update_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    valid: UpdateSuperAdminView,
):
    try:
        orgs_in_scope = check_permission_and_scope(session, "Update", role_modules['update'], current_user)
        selected_entry = session.exec(
            select(db_model).where(db_model.organization.in_(orgs_in_scope["organization_ids"]), db_model.id == valid.id)
        ).first()

        if not selected_entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")
        user_org = session.exec(select(Organization).where(Organization.id == selected_entry.organization)).first() 
        old_username = selected_entry.username
        new_username = add_organization_path(valid.username, user_org.name)
        
        selected_entry.full_name = valid.full_name
        selected_entry.username = new_username
        selected_entry.email = valid.email
        selected_entry.phone_number = valid.phone_number
        if verify_password(valid.old_password + old_username, selected_entry.hashedPassword):
            selected_entry.hashedPassword = get_password_hash(valid.new_password + selected_entry.username)
        else:
            raise HTTPException(status_code=401, detail="Incorrect password")
        if valid.role:
            selected_entry.role = valid.role
        if valid.scope_group:
            selected_entry.scope_group = valid.scope_group       
        session.add(selected_entry)
        session.commit()
        session.refresh(selected_entry)


conf = ConnectionConfig(
    MAIL_USERNAME="sfapwr@bluespark.et",
    MAIL_PASSWORD="Hard&test&work6756",
    MAIL_PORT=465,  # Use 465 for SSL or 587 for STARTTLS
    MAIL_SERVER="mail.bluespark.et",
    MAIL_STARTTLS=False,  # Use True if port 587
    MAIL_SSL_TLS=True,    # Set True for SSL (port 465)
    MAIL_FROM="sfapwr@bluespark.et",  # Ensure this email is valid
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

@c.post("/forgot-Password")
async def send_mail(data: EmailSchema, 
                    db: Session = Depends(get_session),                        
):
    username = data.username

    service_provider = db.exec(select(Organization).where(Organization.organization_type == "Service Provider")).first()

    db_username = add_organization_path(username, service_provider.name)

    # Check if the user exists
    user = db.exec(select(db_model).where(db_model.username == db_username)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    stored_username = add_organization_path(username, service_provider.name)
    #Generate a new random password and hash it
    new_password = generate_random_password()
    hashed_password = get_password_hash(new_password + stored_username)

    #Update user's password in the database
    user.hashedPassword = hashed_password
    db.add(user)
    db.commit()
    db.refresh(user)

    # Build the email template with the generated password included
    template = f"""
<html>
  <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
    <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);">
      
      <div style="text-align: center;">
        <h2 style="color: #0047AB;">Sales Force Automation (SFA)</h2>
        <h4 style="color: #008CBA;">Powered by BlueSpark Business Technology Solutions</h4>
      </div>
      
      <hr style="border: none; height: 1px; background-color: #ddd; margin: 20px 0;">
      
      <p style="font-size: 16px; color: #333;">Hello,</p>
      
      <p style="font-size: 16px; color: #333;">
        Thank you for using <strong>Sales for Automation (SFA)</strong>. We value your trust and are committed to delivering smart solutions for your business efficiency.
      </p>
      
      <p style="font-size: 16px; color: #333;">
        Your New Password is: 
        <span style="font-weight: bold; color: #d9534f; font-size: 18px;">{new_password}</span>
      </p>
      
      <p style="font-size: 16px; color: #333;">
        Please use this password to log in and make sure to update it immediately for security reasons.
      </p>
      
      <hr style="border: none; height: 1px; background-color: #ddd; margin: 20px 0;">
      
      <div style="text-align: center;">
        <p style="font-size: 14px; color: #888;">
          If you have any questions or need assistance, please contact 
          <strong>BlueSpark Business Technology Solutions Support</strong>.
        </p>
      </div>
      
    </div>
  </body>
</html>
"""

    # Prepare the email message. The recipient is now static.
    message = MessageSchema(
        subject="Your New Password",
        recipients=["yalew.tenna@bluespark.et"],
        body=template,
        subtype="html"
    )

    # Send the email
    fm = FastMail(conf)

    await fm.send_message(message)
  
    print(f"New password generated for user : {new_password}")

    return JSONResponse(status_code=200, content={"message": "Email with new password has been sent"})

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
@c.delete(endpoint['delete']+ "/{id}")
def delete_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int
) :
    try:
        orgs_in_scope = check_permission_and_scope(session, "Delete", role_modules['delete'], current_user) 
        selected_entry = session.exec(
            select(db_model).where(db_model.organization.in_(orgs_in_scope["organization_ids"]), db_model.id == id)
        ).first()

        if not selected_entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

        session.delete(selected_entry)
        session.commit()

        return {"message": f"{endpoint_name} deleted successfully"}   
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")