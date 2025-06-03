from pydantic.functional_validators import AfterValidator
from pydantic import BaseModel, root_validator
from typing import Optional
from typing import Annotated
from pydantic import validator
from pydantic import AfterValidator, BaseModel, ValidationError
from utils.util_functions import validate_name, capitalize_name



# class InheritanceView(BaseModel):
#     name: Annotated [ str, AfterValidator( validate_name) ]


class AddInheritanceView(BaseModel):
    name: Annotated[str, AfterValidator(validate_name)]
    category: Optional[int] = None
    product: Optional[int] = None

class UpdateInheritanceView(BaseModel):
    """
    Fields are all optional so you can update the name,
    or the category link, or the product link — any combination.
    """
    id: Optional[int] 

    name: Optional[Annotated[str, AfterValidator(validate_name)]] = None
    # category: Optional[int] = None
    # product: Optional[int] = None

    @root_validator(skip_on_failure=True)
    def at_least_one_field(cls, values):
        if not any(values.get(k) for k in ("name", "category", "product")):
            raise ValueError("At least one of 'name', 'category' or 'product' must be provided")
        return values
 
    

