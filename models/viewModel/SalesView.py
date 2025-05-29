from typing import Optional, Annotated
from datetime import datetime
from pydantic import BaseModel, AfterValidator
from enum import Enum
from models.SalesAndTransactions import OrderStatus, PaymentMode, SalesType, PaymentStates, SalesStates
from utils.util_functions import validate_name

class OrderView(BaseModel):
    employee: int
    sales: Optional[int]
    point_of_sale: int
    date: datetime
    expected_date: Optional[datetime]
    remark: Optional[Annotated [ str,  AfterValidator( validate_name) ] ]
    status: OrderStatus
    total: float
    total_quantity: float

class OrderItemView(BaseModel):
    product: int
    quantity: float
    unit_price: float
    total: float
    employee: int
    order: Optional[int]

class SaleView(BaseModel):
    employee: int
    route: list[int] | dict[int, str] | str
    point_of_sale: int
    date: datetime
    remark: Optional[Annotated [ str,  AfterValidator( validate_name) ] ]
    payment_due_date: datetime
    payment_mode: Optional[PaymentMode]
    sales_type: Optional[SalesType]
    bank: Optional[int]
    cheque: Optional[int]
    discount: float
    payment_status: Optional[PaymentStates]
    payment_date: Optional[datetime]
    total_sales: float
    total_quantity: float
    gross_sales: float
    total_sales_in_words: Optional[Annotated [ str,  AfterValidator( validate_name) ] ] = None
    status: Optional[SalesStates] = None

class SalesTransactionView(BaseModel):
    date: datetime
    sales: int
    amount: float

class SalesItemView(BaseModel):
    sales: Optional[int] = None
    employee: Optional[int] = None
    product: int
    quantity: float
    unit_price: float
    discount: float
    total: float
    before_tax: float

