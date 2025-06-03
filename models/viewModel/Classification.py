from typing import Optional
from typing import Annotated
from pydantic import AfterValidator, BaseModel, ValidationError
from utils.util_functions import validate_name, capitalize_name

class ClassificationView(BaseModel):
    name: Annotated[str, AfterValidator(validate_name)]
    organization: int
    point_of_sale_id: Optional[int] = None
    territory_id: Optional[str] = None
    route_id: Optional[str] = None
    customer_discounts: int = None
    description: Optional[Annotated[str, AfterValidator(validate_name)]]

# class UpdateClassification(BaseModel):
#     id: Optional[int]
#     name: Annotated[str, AfterValidator(validate_name)]
#     sku: Annotated[str, AfterValidator(validate_name)]
#     organization: int
#     category_id: Optional[int] = None
#     image: Optional[str] = None
#     brand: Optional[str] = None
#     price: float
#     unit: Optional[str] = None


