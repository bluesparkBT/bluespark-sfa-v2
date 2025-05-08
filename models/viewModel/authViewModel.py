
from datetime import date
from typing import Optional, Self
from pydantic import Base64Bytes, BaseModel, model_validator
from sqlmodel import SQLModel

from models.Users import Gender
from models.Location import Address
from utils.util_functions import capitalize_name, validate_name


class UserCreation(BaseModel):
    company: int | list[int] | dict[int, str] | None
    organization: list[int] | dict[int, str]
    fullname: str
    username: str
    email: str
    phone_number: str    
    password: str
    role: list[int] | dict[int, str]
    scope: str | list[str] | dict[str, str] | None
    scope_group: str | list[str] | dict[str, str] | None
    
    gender: Gender
    salary: float
    position: str    
    date_of_birth: Optional[str]
    date_of_joining: Optional[str]

    image: str | Base64Bytes | None
    manager: str | dict[int, str] | int | None
    id_type: str
    id_number: str
    house_number: str

    # Address
    country: str
    city: str
    sub_city: str
    woreda: str
    landmark: str

    @model_validator(mode="after")
    def check(self) -> Self:
        if self.date_of_birth == "" or self.date_of_birth == "null":
            self.date_of_birth = None
        if self.date_of_joining == "" or self.date_of_joining == "null":
            self.date_of_joining = None

        if self.organization == "" or self.organization == "null":
            self.organization = None
            
        return self


class UserUpdate(BaseModel):
    organization: list[int] | dict[int, str]
    fullname: str
    username: str
    email: str
    phone_number: str    
    password: str
    role: list[int] | dict[int, str]
    scope: str | list[str] | dict[str, str] | None
    scope_group: str | list[str] | dict[str, str] | None
    
    gender: Gender
    salary: float
    position: str    
    date_of_birth: Optional[str]
    date_of_joining: Optional[str]

    image: str | Base64Bytes | None
    manager: str | dict[int, str] | int | None
    id_type: str
    id_number: str
    house_number: str

    # Address
    country: str
    city: str
    sub_city: str
    woreda: str
    landmark: str

    @model_validator(mode="after")
    def check(self) -> Self:
        if self.date_of_birth == "" or self.date_of_birth == "null":
            self.date_of_birth = None
        if self.date_of_joining == "" or self.date_of_joining == "null":
            self.date_of_joining = None

        if self.organization == "" or self.organization == "null":
            self.organization = None
        return self

class SuperAdminUserCreation(BaseModel):
    fullname: str
    username: str
    email: str
    password: str
    service_provider_company: str | list[str] | dict[str, str] | None

    @model_validator(mode="after")
    def check(self) -> Self:
        if self.service_provider_company == "" or self.service_provider_company == "null":
            self.service_provider_company = None
        return self
    
class SuperAdminUserUpdate(SQLModel, table=False):
    username: str
    email: str
    password: str
    company: str | list[str] | dict[str, str] | None
    scope_group: str | list[str] | dict[str, str] | None

    @model_validator(mode="after")
    def check(self) -> Self:
        if self.service_provider_company == "" or self.service_provider_company == "null":
            self.service_provider_company = None
        return self

class Login(SQLModel, table=False):
    username: str
    password: str


class Token(SQLModel, table=False):
    access_token: str
    token_type: str


class TokenData(SQLModel, table=False):
    username: str | None = None
