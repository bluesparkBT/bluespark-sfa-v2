from typing import Optional
from typing import Annotated
from pydantic import AfterValidator, BaseModel, ValidationError
from utils.util_functions import validate_name, capitalize_name

class CategoryView(BaseModel):
    id: Optional[int] = None
    name: Annotated [ str, AfterValidator( validate_name) ]
    code:  Annotated [ str,  AfterValidator( validate_name) ] 
    description: Optional[str] = None
    parent_category: Optional[int] = None
    organization: int 
