from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import date

class CreditLimitGroup(SQLModel, table=True):
    __tablename__ = "credit_limit_group"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # Credit limit group name
    limit: float  # Maximum credit limit
    time_period: str  # Time period for credit evaluation
    default: bool = Field(default=False)  # Whether this is the default credit group
    status: bool = Field(default=True)  # Active/inactive status
    registered_at: date  # Registration date

    # Relationship with CreditBalanceSheet
    credit_balance_sheets: List["CreditBalanceSheet"] = Relationship(back_populates="credit_limit_group")


class CreditBalanceSheet(SQLModel, table=True):
    __tablename__ = "credit_balance_sheet"

    id: Optional[int] = Field(default=None, primary_key=True)
    balance_left: float  # Remaining credit balance

    point_of_sale_id: int = Field(foreign_key="point_of_sale.id")  # Reference to PointOfSale
    credit_limit_group_id: int = Field(foreign_key="credit_limit_group.id")  # Reference to CreditLimitGroup

    # Relationships
    credit_limit_group: Optional[CreditLimitGroup] = Relationship(back_populates="credit_balance_sheets")