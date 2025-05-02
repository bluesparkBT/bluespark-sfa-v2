from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import uuid4

class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str
    passhash: str
    role_id: Optional[int] = Field(default=None, foreign_key="role.id")
