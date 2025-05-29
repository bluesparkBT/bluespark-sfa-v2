from typing import Optional
from typing import Annotated
from pydantic import Field
from sqlmodel import SQLModel
from utils.util_functions import validate_name, capitalize_name
from pydantic import AfterValidator, BaseModel, ValidationError
        

class TerritoryCreation(BaseModel):
    country: Optional[str] = Field(default="Ethiopia")
    name: Annotated [ str,  AfterValidator( validate_name) ]
    description: Optional[str] = None
    organization: int