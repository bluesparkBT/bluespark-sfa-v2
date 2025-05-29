from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from models.Inheritance import ProductLink, CategoryLink

class Product(SQLModel, table=True):
    __tablename__ = "product"

    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(default=None)
    name: str = Field(default=None, index=True)
    description: Optional[str] = Field(default=None)
    image: Optional[str] = Field(default=None)
    brand: Optional[str] = Field(default=None, index=True)
    batch_number: Optional[str] = Field(default=None, index=True)
    code: str = Field(default=None, index=True)
    price: float = Field(default=None)
    unit: Optional[str] = Field(default=None)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id", index=True)
    category: Optional["Category"] = Relationship(back_populates="products")
    organization_id: Optional[int] = Field(default=None, foreign_key="organization.id", index=True)
    inheritance_groups: List["InheritanceGroup"] = Relationship(back_populates="products", link_model=ProductLink)
    stock: Optional["Stock"] = Relationship(back_populates="product")
    stock_logs: Optional[List["StockLog"]] = Relationship(back_populates="product")
    warehouse_stops: Optional[List["WarehouseStop"]] = Relationship(back_populates="product")




class Category(SQLModel, table=True):
    __tablename__ = "category"  

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(default=None, index=True)
    name: str = Field(default=None, index=True)
    description: Optional[str] = Field(default=None)
    parent_category: Optional [int] = Field(foreign_key = "category.id")
    products: List["Product"] = Relationship(back_populates="category")
    organization_id: Optional [int] = Field(default=None, foreign_key="organization.id", index=True)
    inheritance_groups: List["InheritanceGroup"] = Relationship(back_populates="categories", link_model=CategoryLink)
    category_stocks: List["Stock"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"foreign_keys": "[Stock.category_id]"}
    )
    subcategory_stocks: List["Stock"] = Relationship(
        back_populates="subcategory",
        sa_relationship_kwargs={"foreign_keys": "[Stock.subcategory_id]"}
    )

