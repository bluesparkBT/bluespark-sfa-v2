from typing import Optional, Annotated, Self
from datetime import datetime
from pydantic import BaseModel, AfterValidator, model_validator
from enum import Enum
from models.SalesAndTransactions import PenetrationStatus
from utils.util_functions import validate_email, validate_name, validate_phone_number

class PenetrationCreation(BaseModel):
    company_name: Annotated [ str,  AfterValidator( validate_name) ] 
    outlet_name: str
    channel: Optional[str]
    tin: str
    phone: Annotated [ str,  AfterValidator( validate_phone_number) ] 
    email: str
    address: int
    location: int
    employee: int
    status: PenetrationStatus

    @model_validator(mode="after")
    def check(self) -> Self:
        if self.channel == "null" or self.channel == "":
            self.channel = None
        if self.tin == "null" or self.tin == "":
            self.tin = None
        else:
            if len(self.tin) != 10 or not self.tin.isdigit():
                raise ValueError("TIN must be 10 numbers long and only digits")
            if self.tin[0] != "0" or self.tin[1] != "0":
                raise ValueError("TIN must start with 00")

        return self
