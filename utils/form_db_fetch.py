from sqlmodel import select
from fastapi import Request, HTTPException, status, Depends
from typing import Annotated
from db import  get_session
from models.Account import (
    Organization,
    User,
    Role,
    ScopeGroup
)

from sqlmodel import Session, select

SessionDep = Annotated[Session, Depends(get_session)]
def fetch_user_id_and_name(session: SessionDep):
    
    users_row = session.exec(select(User.id, User.fullname)).all()
    users = {row[0]: row[1] for row in users_row}
    return users

def fetch_organization_id_and_name(session: SessionDep):
    
    organization_row = session.exec(select(Organization.id, Organization.organization_name)).all()
    organizations = {int(row[0]): row[1] for row in organization_row}
    return organizations

def fetch_role_id_and_name(session: SessionDep):
    
    role_row = session.exec(select(Role.id, Role.name)).all()
    roles = {row[0]: row[1] for row in role_row}
    return roles

def fetch_scope_group_id_and_name(session: SessionDep):
    
    scope_group_row = session.exec(select(ScopeGroup.id, ScopeGroup.scope_name)).all()
    scope_groups = {row[0]: row[1] for row in scope_group_row}
    return scope_groups

