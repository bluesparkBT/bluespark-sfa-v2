from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import date
from models.Account import Organization
from models.Product_Category import ClassificationLink,InheritanceGroup


class ClassificationGroup(SQLModel, table=True):
    __tablename__ = "classification_group"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    organization: int = Field(foreign_key="organization.id", ondelete="CASCADE")  # Reference to Organization
    point_of_sale_id: Optional[int] = Field(default=None, foreign_key="point_of_sale.id")
    territory_id: Optional[int] = Field(default=None, foreign_key="territory.id")
    route_id: Optional[int] = Field(default=None, foreign_key="route.id")
    # A classification group can have many discount entries.
    customer_discounts: int = Field(foreign_key="customer_discount.id")  # Reference to Organization
    inheritance_groups: List["InheritanceGroup"] = Relationship(back_populates="classifications", link_model=ClassificationLink)
    description: Optional[str] = Field(default=None)


class CustomerDiscount(SQLModel, table=True):
    __tablename__ = "customer_discount"

    id: Optional[int] = Field(default=None, primary_key=True)
    # Defines the validity period for the discount
    start_date: date = Field()
    end_date: date = Field()

    # The discount amount or percentage applied to customers of the classification.
    discount: float = Field(description="Discount amount or percentage applicable.")

class PromotionalItem(SQLModel, table=True):
    __tablename__ = "promotional_item"

    """
    Represents a promotional item scheduled for distribution as part of a route schedule.

    This class stores information about promotional items, including the product being promoted,
    the total quantity scheduled for promotion, and the route schedule to which the item belongs.
    Promotional items are used to increase product visibility, drive sales, and incentivize purchases.

    Attributes:
        id (Optional[int]): Unique identifier of the promotional item (primary key).
        product (int): The ID of the product being promoted (foreign key to product.id).
        totalScheduled (int): The total quantity of the item scheduled for promotion.
        routeSchedule (int): The ID of the route schedule this item is part of (foreign key to route_schedule.id).
        active (bool): Indicates whether the item is active (default: True).
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    promotionImage: Optional[str] = Field(default=None)
    product: int = Field(foreign_key="product.id", index=True)
    quantity: float = Field(default=0)
    promotion: Optional[int] = Field(foreign_key="promotion.id", default=None, index=True)
    employee_id: int = Field(foreign_key="users.id", index=True)
    promotion_id:int = Field(foreign_key="promotion.id", index=True)
    promotion: Optional["Promotion"] = Relationship(back_populates="promotional_items")
    
class Promotion(SQLModel, table=True):
    __tablename__ = "promotion"
    id: Optional[int] = Field(default=None, primary_key=True)
    territory: int = Field(foreign_key="territory.id", index=True)
    route: Optional[int] = Field(default=None, foreign_key="route.id", index=True)
    point_of_sale: Optional[int] = Field(default=None, foreign_key="point_of_sale.id", index=True)
    promotional_items: Optional[List[PromotionalItem]]= Relationship(back_populates= "promotion")

class ShelfShare(SQLModel, table=True):
    """
    ShelfShare represents a record capturing the shelf share details.
    
    Attributes:
      id: Primary key identifier.
      shelfShareImage: Stores the image data associated with this shelf share.
                        (Option 1: as binary data using LargeBinary. Alternatively, store as a URL/string.)
      competitor_id: Foreign key reference to a Competitor record.
      point_of_sale_id: Foreign key reference to a PointOfSale record.
      estimated_own_products: Numeric value estimating how many of the company's own products are on the shelf.
      estimated_competitors_products: Numeric value estimating how many competitor products are on the shelf.
    """
    __tablename__ = "shelf_share"

    id: Optional[int] = Field(default=None, primary_key=True)

    shelfShareImage: Optional[str]= Field(default=None)
    competitor: str = Field(default=None)
    point_of_sale_id: int = Field(foreign_key="point_of_sale.id", index=True)
    estimated_own_products: int = Field(default=0)
    estimated_competitors_products: int = Field(default=0)

class SalesActivation(SQLModel, table=True):
    __tablename__ = "sales_activation"

    """
    Represents the activation of a promotion for a specific route schedule.

    This class stores information about the activation of promotions, including the route schedule ID,
    the promotion ID, and the date of activation. Promotion activations are used to track when promotions
    are made active for specific routes or schedules.

    Attributes:
        id (Optional[int]): Unique identifier of the promotion activation (primary key).
        routeSchedule (int): The ID of the route schedule for which the promotion is activated (foreign key to route_schedule.id).
        promotion (int): The ID of the promotion being activated (foreign key to promotion.id).
        dateActivated (datetime): The date and time when the promotion was activated (default: current time).
        active (bool): Indicates whether the activation is active (default: True).
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    sale: Optional[int] = Field(default=None, foreign_key="sale.id", index=True)
    quantity: float = Field(default=0)
    promotion: int = Field(foreign_key="promotion.id", index=True)
    distance: int = Field(foreign_key="geolocation.id")
