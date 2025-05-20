from typing import Annotated, List, Dict, Any, Optional
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from utils.model_converter_util import get_html_types
from models.Territory import Territory, Route
from models.Inheritance import InheritanceGroup
from utils.util_functions import validate_name
from models.Account import Organization
from utils.auth_util import get_current_user, check_permission
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_category_id_and_name, fetch_organization_id_and_name
import traceback


CatagoryRouter = terr = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]



#@terr.get("/get-territory"):
# def get_territory(
#     Session: SessionDep,
#     current_user: UserDep,
#     tenant: str,
# ):
#     try:
#         if not check_permission(
#             session, "Read",  ["Administrative", "Product"], current_user
#             ):
#             raise HTTPException(
#                 status_code=403, detail="You Do not have the required privilege"
#             )

#         organization_categories = session.exec(
#             select(Territory).where(Territory.organization_id == current_user.organization_id)
#         ).all()
         
# @terr.post("create-territory"):
# def create_territory(
#     Session: SessionDep,
#     current_user: UserDep,
#     tenant: str 
#     ,
#     country: str = Body(...),
#     name: str = Body(...),
#     description: str= Body(...),
#     organization: int = Body(...),
#     routes:




#     ):

    
    
