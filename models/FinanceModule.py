from datetime import datetime
from enum import Enum
from pydantic import Base64Bytes, model_validator
from sqlmodel import Relationship, SQLModel, Field
from typing import List, Optional, Self


class BankAccount(SQLModel, table=True):
    __tablename__ = "bank_account"

    """
    Represents a bank account held by an organization.

    This class stores details about an organization's bank account,
    including the bank's name, the account number, and whether the
    account is currently active. It also links the bank account to
    the organization that owns it.

    Attributes:
        id (Optional[integer]): The unique identifier for this bank account.
            This is automatically generated by the database.
        bank_name (string): The name of the banking institution. This field
            is indexed for faster lookups.
        account (string): The account number. This field is also indexed.
        branch (Optional[string]): The specific branch of the bank where the
            account is held.
        account_holder (Optional[string]): The name of the account holder, which
            is usually the organization name.
        organization (Optional[integer]): Foreign key linking this bank account
            to the `Organization` table. This indicates which organization owns
            this bank account and is indexed for efficient querying.
        active (boolean): A boolean flag indicating whether this bank account is
            currently active and in use. Defaults to True.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_name: str = Field(index=True)
    account: str = Field(index=True)
    account_holder: Optional[str] = Field(default=None)
    organization: Optional[int] = Field(foreign_key="organization.id", index=True)


class Cheque(SQLModel, table=True):
    __tablename__ = "cheque"
    
    """
    Represents a cheque payment.

    This class stores information about a cheque, including its number,
    the owner, the date it was issued, and the amount. It is intended
    to be linked to sales records where payment is made via cheque.

    Attributes:
        id (Optional[integer]): The unique identifier for this cheque record.
            Automatically generated by the database.
        cheque_number (string): The unique number printed on the cheque.
        check_owner (string): The name of the person or entity that issued the cheque.
        check_date (datetime): The date printed on the cheque. Defaults to the
            current date and time and is indexed for querying by date.
        amount (float): The monetary value of the cheque.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    cheque_number: str
    check_owner: str
    check_date: datetime = Field(default=datetime.now(), index=True)
    amount: float


class DepositStatus(str, Enum):
    """
    Represents the status of a deposit.

    Members:
        pending: The deposit is new and pending.
        approved: The deposit has been approved.
        rejected: The deposit has been rejected.
    """

    Pending = "Pending"
    Approved = "Approved"
    Rejected = "Rejected"


class Deposit(SQLModel, table=True):
    __tablename__ = "deposit"

    """
    Represents a deposit made by an employee into a bank account (organization bank account).

    This class records details of deposits made by employees, including
    the employee who made the deposit, the date, bank details, the
    amount deposited, and any relevant remarks. It can be linked to
    sales transactions to track payments.

    Attributes:
        id (Optional[integer]): The unique identifier for this deposit record.
            Automatically generated by the database.
        employee (integer): Foreign key linking this deposit to the `Employee`
            table, indicating which employee made the deposit. This field is
            indexed.
        date (datetime): The date when the deposit was made. Defaults to the
            current date and time and is indexed for querying by date.
        bank (integer): Foreign key linking this deposit to The Bank Account of the organization where the deposit was made.
        amount (float): The amount of money deposited.
        remark (Optional[string]): Any additional notes or information related to
            this deposit.
        active (boolean): A boolean flag indicating whether this deposit record is
            currently considered active. Defaults to True.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    sales_representative: int = Field(foreign_key="users.id", index=True)
    approver: Optional[int] = Field(foreign_key="users.id", index=True, default=None)
    date: datetime = Field(default=datetime.now(), index=True)
    bank: int = Field(foreign_key="bank_account.id", index=True)
    branch: Optional[str] = Field(default=None)
    amount: float
    remark: Optional[str] = Field(default=None)
    approval_status: DepositStatus = Field(default=DepositStatus.Pending)
    deposit_slip: Optional[Base64Bytes] = Field(default=None)
    transaction_number: Optional[str] = Field(default=None)
    organization: Optional[int] = Field(foreign_key="organization.id", index=True)
