from sqlmodel import select
from fastapi import Request, HTTPException, status, Depends
from typing import Annotated
from db import  get_session
from models.Account import (
    User
)

from sqlmodel import Session, select

SessionDep = Annotated[Session, Depends(get_session)]
def fetch_user_id_and_name(session: SessionDep):
    
    users_row = session.exec(select(User.id, User.fullname)).all()
    users = {row[0]: row[1] for row in users_row}
    return users


