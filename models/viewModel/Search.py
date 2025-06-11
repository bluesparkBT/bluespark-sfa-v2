from typing import Optional
from typing import Annotated
from pydantic import Field
from sqlmodel import SQLModel
from utils.util_functions import validate_name, capitalize_name
from pydantic import AfterValidator, BaseModel, ValidationError
from datetime import datetime


class SearchPagination(BaseModel):
    page: int 
    pageSize: int
    searchString: str