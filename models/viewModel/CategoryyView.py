from enum import Enum
from typing import List, Optional
from typing import Annotated

from sqlmodel import SQLModel
from models.Product_Category import Category

from models.Product_Category import Category, Product, InheritanceGroup, ProductLink, CategoryLink
from pydantic import AfterValidator, BaseModel, ValidationError
from utils.util_functions import validate_name, capitalize_name

class CategoryView(BaseModel):
    id: Optional[int] = None
    name: Annotated [ str, AfterValidator( validate_name) ]
    code:  Annotated [ str,  AfterValidator( validate_name) ] 
    description: Optional[str] = None
    parent_category: Optional[int] = None
    organization_id: int 

    # parent_category: Optional[str] = None