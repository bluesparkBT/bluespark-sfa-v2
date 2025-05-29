from datetime import datetime
from enum import Enum
from pydantic import model_validator
from sqlmodel import SQLModel, Field
from typing import Optional, Self


class NatureOfComplaint(str, Enum):
    """
    Enum class representing the nature of a complaint.

    This enum provides a standardized set of categories for classifying complaints,
    allowing for easier analysis and reporting.

    Attributes:
        none: Represents no specific nature of complaint.
        quality: Represents a complaint related to the quality of a product.
        foodSafety: Represents a complaint related to the food safety of a product.
    """

    quality = "Quality"
    packaging = "Packaging"
    coloring = "Coloring"
    foodSafety = "Food Safety"


class Complaint(SQLModel, table=True):
    __tablename__ = "complaint"

    """
    SQLModel class representing a customer complaint record in the database.

    This class defines the structure of the 'complaint' table, including fields
    for the complaint's ID, date, associated employee and point of sale,
    nature of the complaint, and active status.

    Attributes:
        id: Optional[int] - The unique identifier of the complaint (primary key).
        date: datetime - The date and time when the complaint was created (default: current time).
        employee: int - The ID of the employee who handled the complaint (foreign key to users.id).
        point_of_sale: int - The ID of the point of sale where the complaint originated (foreign key to point_of_sale.id).
        natureOfComplaint: NatureOfComplaint - The nature of the complaint (enum).
        active: bool - A boolean indicating whether the complaint is active (default: True).
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    date: datetime = Field(default=datetime.now(), index=True)
    employee: int = Field(foreign_key="users.id", index=True)
    point_of_sale: int = Field(foreign_key="point_of_sale.id", index=True)
    nature_of_complaint: NatureOfComplaint


class IssueType(str, Enum):
    """
    Enumeration representing the type of issue associated with a complaint item.

    This enum provides a set of predefined issue types to categorize the specific
    problem reported in a complaint item, such as product defects, packaging issues,
    or medical concerns.

    Attributes:
        Product Issue: Represents an issue related to the product itself.
        Packaging Issue: Represents an issue related to the product's packaging.
        Medical Issue: Represents a medical issue caused by the product.
        other: Represents any other type of issue.
    """

    productIssue = "Product Issue"
    packagingIssue = "Packaging Issue"
    medicalIssue = "Medical Issue"
    other = "Other"


class ComplaintItem(SQLModel, table=True):
    __tablename__ = "complaint_item"

    """
    SQLModel class representing an item associated with a customer complaint.

    This class defines the structure of the 'complaint_item' table, which stores
    details about specific issues reported within a complaint, such as the issue type,
    description, related product, lot number, quantity, and the complaint it belongs to.

    Attributes:
        id: Optional[int] - The unique identifier of the complaint item (primary key).
        issueType: IssueType - The type of issue (enum, default: Product Issue).
        description: Optional[str] - A description of the issue (default: None).
        product: int - The ID of the product related to the issue (foreign key to product.id).
        lotNumber: str - The lot number of the product (indexed).
        quantity: int - The quantity of the product affected by the issue.
        complaintId: int - The ID of the complaint this item belongs to (foreign key to complaint.id).
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    issue_type: IssueType = Field(default=IssueType.productIssue)
    description: Optional[str] = Field(default=None)
    product: int = Field(foreign_key="product.id", index=True)
    batch_number: str = Field(index=True)
    quantity: int
    complaint: int = Field(foreign_key="complaint.id", index=True)

