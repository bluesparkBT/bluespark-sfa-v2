from pydantic.functional_validators import AfterValidator
from pydantic import BaseModel, root_validator
from typing import Optional, Any
from typing import Annotated, List
from pydantic import AfterValidator, BaseModel, field_validator
from utils.util_functions import validate_name, capitalize_name

class InheritanceView(BaseModel):
    name: Annotated[str, AfterValidator(validate_name)]
    organization: Optional[int] =None
    category: Optional[List[int]] = None
    product: Optional[List[int]] = None
    role: Optional[List[int]] = None
    # classification: Optional[List[int]] = None
    # point_of_sale: Optional[List[int]] = None

    @field_validator("category", "product", "role", mode="before")
    @classmethod
    def ensure_list(cls, v: Any):
        if v is None:
            return v
        if isinstance(v, list):
            return v
        return [v]
    
class UpdateInheritanceView(BaseModel):
    id: Optional[int] 
    name: Optional[Annotated[str, AfterValidator(validate_name)]] = None
    organization: Optional[int] =None
    category: Optional[List[int]] = None
    product: Optional[List[int]] = None
    role: Optional[List[int]] = None
    # classification: Optional[List[int]] = None
    # point_of_sale: Optional[List[int]] = None

    @field_validator("category", "product", "role", mode="before")
    @classmethod
    def ensure_list(cls, v: Any):
        if v is None:
            return v
        if isinstance(v, list):
            return v
        return [v]