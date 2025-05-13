from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional


class Product(SQLModel, table=True):
    __tablename__ = "product"

    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(default=None)
    name: str = Field(default=None, index=True)
    description: Optional[str] = Field(default=None)
    image: Optional[str] = Field(default=None)
    brand: Optional[str] = Field(default=None, index=True)
    batch_number: Optional[str] = Field(default=None, index=True)
    code: Optional[str] = Field(default=None, index=True)
    price: Optional[float] = Field(default=None)
    unit: Optional[str] = Field(default=None)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id", index=True)
    category: Optional["Category"] = Relationship(back_populates="products")


class Category(SQLModel, table=True):
    __tablename__ = "category"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: int = Field(default=None, index=True)
    name: str = Field(default=None, index=True)
    description: Optional[str] = Field(default=None)
    products: List["Product"] = Relationship(back_populates="category")
