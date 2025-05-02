from datetime import  datetime
from models.User import Gender, IdType
from pydantic import model_validator, validate_email
from sqlmodel import SQLModel, Field
from typing import Optional, Self
from enum import Enum


from utils.util_functions import capitalize_name, is_valid_phone_number



class User(SQLModel, table=True):
    __tablename__ = "sfa_user"
    """
     Represents a user in the system.

    This class defines the structure for storing user information, including their username, full name, email, password,
    and phone number. It also includes additional optional fields for date of birth, joining date, salary, position,
    ID type and number, gender, and address. It includes validation logic to ensure the integrity of user data.

    Attributes:
        id (Optional[int]): Unique identifier of the user (primary key).
        fullname (str): The full name of the user (indexed).
        username (str): The username of the user (indexed and unique).
        email (Optional[str]): The email address of the user (indexed).
        phone (str): The phone number of the user (indexed).
        password (str): The password of the user.
        date_of_birth (Optional[datetime]): The date of birth of the user.
        date_of_joining (Optional[datetime]): The date the user joined the system.
        salary (Optional[float]): The salary of the user.
        position (Optional[str]): The job position of the user.
        id_type (Optional[IdType]): The type of identification document.
        id_number (Optional[str]): The identification number.
        gender (Optional[Gender]): The gender of the user.
        address (Optional[int]): Foreign key referencing the user's address ID (indexed).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    fullname: str = Field(index=True)
    username: str = Field(unique=True, index=True)
    email: Optional[str] = Field(index=True)
    phone: str = Field(index=True)
    password: str
    date_of_birth: Optional[datetime] = Field(default=None)
    date_of_joining: Optional[datetime] = Field(default=None)
    salary: Optional[float] = Field(default=None)
    position: Optional[str] = Field(default=None)
    id_type: Optional[IdType] = Field(default=None)
    id_number: Optional[str] = Field
    gender: Optional[Gender]
    # manager: Optional[int] = Field(default=None, foreign_key="employee.id")
    country: str = Field(default="Ethiopia", index=True)
    city: str = Field(index=True)
    sub_city: str = Field(index=True)
    woreda: str = Field(index=True)
    landmark: Optional[str] = Field(default=None, index=True)



    @model_validator(mode="after")
    def check(self) -> Self:

        if validate_email(self.email) is False:
            raise ValueError("Invalid email")

        if is_valid_phone_number(self.phone) is False:
            raise ValueError("Invalid phone number")

        if self.date_of_birth == "" or self.date_of_birth == "null":
            self.date_of_birth = None

        if self.date_of_joining == "" or self.date_of_joining == "null":
            self.date_of_joining = None
       
        # if self.manager == "" or self.manager == "null":
        #     self.manager = None
       
       

        return self