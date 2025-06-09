from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum
from models.FinanceModule import DepositStatus
from models.SalesAndTransactions import InvoiceTypes, InvoiceStates

# Finance Module View Models

class BankAccountView(BaseModel):
    bank_name: str
    account: str
    account_holder: Optional[str]
    organization: Optional[int]


class UpdateBankAccountView(BaseModel):
    id: Optional[int]
    bank_name: str
    account: str
    account_holder: Optional[str]
    organization: Optional[int]

class ChequeView(BaseModel):
    cheque_number: str
    check_owner: str
    check_date: datetime
    amount: float

class DepositView(BaseModel):
    # sales_representative: int
    bank: str
    account: Optional[int | str]
    branch: Optional[str]
    amount: float
    remark: Optional[str]
    date: datetime
    organization: Optional[int]   
    transaction_number: Optional[str] 
    deposit_slip: Optional[bytes]

    
class UpdateDepositView(BaseModel):
    id:Optional[int]
    # sales_representative: int
    bank: str
    account: int | str
    branch: Optional[str]
    amount: float
    remark: Optional[str]
    date: datetime
    organization: Optional[int] 
    transaction_number: Optional[str]   
    deposit_slip: Optional[bytes]

class InvoiceView(BaseModel):
    number: int
    type: InvoiceTypes
    status: InvoiceStates
    remark: Optional[str]
    date: datetime
    sales: int
    organization: Optional[int]