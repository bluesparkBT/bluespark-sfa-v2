from typing import Optional, Annotated, Self
from datetime import datetime
from pydantic import BaseModel, AfterValidator, model_validator
from enum import Enum
from models.SalesAndTransactions import PenetrationStatus
from utils.util_functions import validate_email, validate_name, validate_phone_number
from models.Complaint import NatureOfComplaint, IssueType

class ComplaintCreation(BaseModel):
    
    employee: int
    date: datetime
    point_of_sale: int
    nature_of_complaint: NatureOfComplaint


class ComplaintItemCreation(BaseModel):
    issue_type: IssueType
    description: Annotated [ str,  AfterValidator( validate_name) ] 
    product: int
    batch_number: str
    quantity: int
    complaint: int


    @model_validator(mode="after")
    def check(self) -> Self:
        if self.description == "null" or self.description == "":
            self.description = None
        return self