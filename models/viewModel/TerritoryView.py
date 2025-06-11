from typing import Optional
from typing import Annotated
from pydantic import Field
from sqlmodel import SQLModel
from utils.util_functions import validate_name, capitalize_name
from pydantic import AfterValidator, BaseModel, ValidationError
        

class TerritoryView(BaseModel):
    country: str = Field(default="Ethiopia", index=True)  # Default value retained
    name: Annotated[str, AfterValidator(validate_name)]
    description: Optional[str]
    organization: int

class UpdateTerritoryView(BaseModel):
    id: Optional[int]
    country: str
    name: Annotated[str, AfterValidator(validate_name)]
    description: Optional[str]
    organization: int


class RouteView(BaseModel):
    name: Annotated[str, AfterValidator(validate_name)]
    territory: int
    description: Optional[str]
    organization: int

class updateRouteView(BaseModel):
    id: Optional[int]
    name: Annotated[str, AfterValidator(validate_name)]
    territory: int
    description: Optional[str]
    organization: int