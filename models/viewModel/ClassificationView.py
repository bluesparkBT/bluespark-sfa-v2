from typing import Optional
from typing import Annotated
from pydantic import AfterValidator, BaseModel, ValidationError
from utils.util_functions import validate_name, capitalize_name
from datetime import datetime

# Define validation function if needed
def validate_discount(value: float) -> float:
    if value < 0:
        raise ValueError("Discount must be a positive number.")
    return value

class ClassificationView(BaseModel):
    name: Annotated[str, AfterValidator(validate_name)]
    organization: int
    point_of_sale: Optional[int] = None
    route: Optional[int] = None
    territory: Optional[int] = None
    description: Optional[Annotated[str, AfterValidator(validate_name)]]
    
    start_date: datetime
    end_date: datetime
    discount: Annotated[float, AfterValidator(validate_discount)]


class updateClassificationView(BaseModel):
    id: Optional[int]
    name: Annotated[str, AfterValidator(validate_name)]
    organization: int
    point_of_sale: Optional[int] = None
    territory: Optional[int] = None
    route: Optional[int] = None
    description: Optional[Annotated[str, AfterValidator(validate_name)]]
    
    customer_id: int = None
    start_date: datetime
    end_date: datetime
    discount: Annotated[float, AfterValidator(validate_discount)]



class CustomerDiscountView(BaseModel):
    id: int | str
    start_date: datetime
    end_date: datetime
    discount: Annotated[float, AfterValidator(validate_discount)]

class UpdateCustomerDiscountView(BaseModel):
    id: Optional[int]
    start_date: datetime
    end_date: datetime
    discount: Annotated[float, AfterValidator(validate_discount)]


