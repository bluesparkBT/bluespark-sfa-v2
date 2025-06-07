from typing import Optional
from typing import Annotated
from pydantic import AfterValidator, BaseModel, ValidationError
from utils.util_functions import validate_name, capitalize_name

class ProductView(BaseModel):
    name: Annotated[str, AfterValidator(validate_name)]
    sku: Annotated[str, AfterValidator(validate_name)]
    organization: int
    category: Optional[int] = None
    image: Optional[str] = None
    brand: Optional[str] = None
    price: float
    unit: Optional[str] = None
    description: Optional[Annotated[str, AfterValidator(validate_name)]]

class UpdateProductView(BaseModel):
    id: Optional[int]
    name: Annotated[str, AfterValidator(validate_name)]
    sku: Annotated[str, AfterValidator(validate_name)]
    organization: int
    category: Optional[int] = None
    image: Optional[str] = None
    brand: Optional[str] = None
    price: float
    unit: Optional[str] = None
    description: Optional[Annotated[str, AfterValidator(validate_name)]]


class CategoryView(BaseModel):
    name: Annotated [ str, AfterValidator( validate_name) ]
    code:  Annotated [ str,  AfterValidator( validate_name) ] 
    description: Optional[str] = None
    parent_category: Optional[int] = None
    organization: Optional[int] 

class UpdateCategoryView(BaseModel):
    id: Optional[int] = None
    name: Annotated [ str, AfterValidator( validate_name) ]
    code:  Annotated [ str,  AfterValidator( validate_name) ] 
    description: Optional[str] = None
    parent_category: Optional[int] = None
    organization: Optional[int] 
