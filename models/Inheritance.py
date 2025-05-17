from sqlmodel import SQLModel, Field, Relationship
from enum import Enum   
from typing import Optional, List

class ProductLink(SQLModel, table=True):
    __tablename__ = "product_link"

    id: Optional[int] = Field(default=None, primary_key=True)
    inheritance_group_id: int = Field(foreign_key="inheritance_group.id", index=True)
    product_id: int = Field(foreign_key="product.id", index=True)

class CategoryLink(SQLModel, table=True):
    __tablename__ = "category_link"

    id: Optional[int] = Field(default=None, primary_key=True)
    inheritance_group_id: int = Field(foreign_key="inheritance_group.id", index=True)
    category_id: int = Field(foreign_key="category.id", index=True)
   
class InheritanceGroup(SQLModel, table=True):
    __tablename__ = "inheritance_group"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True)

    products: List["Product"] = Relationship(back_populates="inheritance_groups", link_model=ProductLink)

    categories: List["Category"] = Relationship(back_populates="inheritance_groups", link_model=CategoryLink)

