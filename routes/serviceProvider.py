from typing import Annotated, List, Dict, Any, Optional, Union
from db import SECRET_KEY, get_session, engine
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from models.viewModel.AccountsView import EmailSchema

from datetime import datetime, timedelta
import requests

from fastapi_mail import FastMail, MessageSchema,ConnectionConfig
from starlette.requests import Request
from starlette.responses import JSONResponse
from pydantic import EmailStr, BaseModel
from utils.auth_util import (
    get_current_user,
    check_permission,
    check_permission_and_scope,
    generate_random_password,
    get_password_hash,
    add_organization_path,
    verify_password,
    create_access_token
)
from utils.model_converter_util import get_html_types
from models.Account import User, ScopeGroup,ScopeGroupLink, Organization, Role
from utils.util_functions import validate_name
from models.viewModel.AccountsView import UserAccountView as TemplateView
from utils.auth_util import get_current_user, check_permission, check_permission_and_scope
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_category_id_and_name, fetch_organization_id_and_name, fetch_id_and_name
import traceback


endpoint_name = "superadmin"

db_model = User

endpoint = {
    "get": f"/get-{endpoint_name}",
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

ServiceProvider = c = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]

UserDep = Annotated[dict, Depends(get_current_user)]


#Authentication Related
@c.get("/has-superadmin")
def has_superadmin_created(
    session: SessionDep
) ->bool:
    existing_superadmin = session.exec(select(db_model).where(db_model.role_id == Role.id == "Super Admin")).first()
    if existing_superadmin:
        print("Super admin and tenant already exists")
        return True
    else: 
        return False
        
@c.post("/login/")
def login(
    session: SessionDep,
    
    username: str = Body(...),
    password: str = Body(...)
):
    try:
        service_provider = session.exec(select(Organization).where(Organization.organization_type == "Service Provider")).first()
        db_username = add_organization_path(username, service_provider.organization_name)

        user = session.exec(select(db_model).where(db_model.username == db_username)).first()
        if not user or not verify_password(password+db_username, user.hashedPassword):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
        access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
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
        traceback.print_exc()
        return {"error": str(e)}
        
#CRUD
@c.get(endpoint['get'])
def get_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str

):
    
    try:  
        orgs_in_scope = check_permission_and_scope(session, "Read", role_modules['get'], current_user)
        
        entries_list = session.exec(
            select(db_model).where(db_model.organization_id.in_(orgs_in_scope["organization_ids"]))
        ).all()

        return entries_list

    except Exception as e:
        traceback.print_exc()
 
@c.get(endpoint['get_by_id'] + "/{id}")
def get_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int,
    # valid: TemplateView,
):
    try:
        if not check_permission(
            session, "Read",[ "Category", "Administrative"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        # Fetch categories based on organization IDs
        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        entry = session.exec(
            select(db_model).where(db_model.organization_id.in_(organization_ids), db_model.id == id)
        ).first()

        if not entry:
            raise HTTPException(status_code=404, detail="Category not found")
        

        return entry
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
@c.post(endpoint['create'])
def create_template(
    session: SessionDep,
    #tenant: str,
    #current_user: UserDep,
    valid: TemplateView,
):
    try:
        
        #if not check_permission(
        #    session, "Create", role_modules['create'], current_user
        #    ):
        #    raise HTTPException(
        #        status_code=403, detail="You Do not have the required privilege"
        #    )
        #organization_ids = get_organization_ids_by_scope_group(session, current_user)

        # Create a new category entry from validated input

        new_entry = db_model.model_validate(valid)        
        
        session.add(new_entry)
        session.commit()
        session.refresh(new_entry)

        return new_entry

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
 
# update a single category by ID
@c.post(endpoint['update'])
def update_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    valid: TemplateView,
):
    try:
        # Check permission
        if not check_permission(
            session, "Update",role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        # Fetch categories based on organization IDs
        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        selected_entry = session.exec(
            select(db_model).where(db_model.organization_id.in_(organization_ids), db_model.id == valid.id)
        ).first()

        if not selected_entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")
        
        if valid.organization == organization_ids:
            selected_entry.organization_id = valid.organization
        else:
            {"message": "invalid input select your own organization id"}    
 
        # Commit the changes and refresh the object
        session.add(valid)
        session.commit()
        session.refresh(valid)

        return {"message": f"{endpoint_name} Updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    

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
async def send_mail(data: EmailSchema, db: Session = Depends(get_session)):
    # username = data.username

    # # Check if the user exists
    # user = db.exec(select(User).where(User.username == username)).first()
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")

    # # Retrieve the user's role using their role_id
    # role = db.exec(select(Role).where(Role.id == user.role_id)).first()
    # if not role or role.name != "SuperAdmin":
    #     raise HTTPException(
    #         status_code=403, detail="Access denied. Only SuperAdmins can request new passwords."
    #     )

    # Generate a new random password and hash it
    new_password = generate_random_password()
    hashed_password = get_password_hash(new_password)

    # Update user's password in the database
    # user.hashedPassword = hashed_password
    # db.add(user)
    # db.commit()
    # db.refresh(user)

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
        recipients=["mikasol9134@gmail.com"],
        body=template,
        subtype="html"
    )

    # Send the email
    fm = FastMail(conf)

    await fm.send_message(message)
  
    print(f"New password generated for user : {new_password}")

    return JSONResponse(status_code=200, content={"message": "Email with new password has been sent"})


# Delete a category by ID
@c.delete(endpoint['delete']+ "/{id}")
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
        # Fetch categories based on organization IDs
        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        selected_entry = session.exec(
            select(db_model).where(db_model.organization_id.in_(organization_ids), db_model.id == id)
        ).first()

        if not selected_entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

    
        # Delete category after validation
        session.delete(selected_entry)
        session.commit()

        return {"message": f"{endpoint_name} deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



