from typing import Optional
from typing import Annotated
from pydantic import AfterValidator, BaseModel, ValidationError
from utils.util_functions import validate_name, capitalize_name
from datetime import date

class ClassificationView(BaseModel):
    name: Annotated[str, AfterValidator(validate_name)]
    organization: int
    point_of_sale_id: Optional[int] = None
    territory_id: Optional[int] = None
    route_id: Optional[int] = None
    customer_discounts: Optional[int] = None
    description: Optional[Annotated[str, AfterValidator(validate_name)]]

class updateClassificationView(BaseModel):
    id: Optional[int]
    name: Annotated[str, AfterValidator(validate_name)]
    organization: int
    point_of_sale: Optional[int] = None
    territory: Optional[int] = None
    route: Optional[int] = None
    customer_discount: Optional[int] = None
    description: Optional[Annotated[str, AfterValidator(validate_name)]]


# Define validation function if needed
def validate_discount(value: float) -> float:
    if value < 0:
        raise ValueError("Discount must be a positive number.")
    return value

class CustomerDiscountView(BaseModel):
    id: int | str
    start_date: date
    end_date: date
    discount: Annotated[float, AfterValidator(validate_discount)]

class UpdateCustomerDiscountView(BaseModel):
    id: Optional[int]
    start_date: date
    end_date: date
    discount: Annotated[float, AfterValidator(validate_discount)]


