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

class ChequeView(BaseModel):
    cheque_number: str
    check_owner: str
    check_date: datetime
    amount: float

class DepositView(BaseModel):
    sales_representative: int
    approver: Optional[int]
    date: datetime
    bank: int
    branch: Optional[str]
    amount: float
    remark: Optional[str]
    approval_status: DepositStatus
    deposit_slip: Optional[bytes]
    organization: Optional[int]

class InvoiceView(BaseModel):
    number: int
    type: InvoiceTypes
    status: InvoiceStates
    remark: Optional[str]
    date: datetime
    sales: int
    organization: Optional[int]