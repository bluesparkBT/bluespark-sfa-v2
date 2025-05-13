from sqlmodel import SQLModel, Field, Relationship
from enum import Enum   
from typing import Optional, List

class ProductLink(SQLModel, table=True):
    __tablename__ = "product_link"

    id: Optional[int] = Field(default=None, primary_key=True)
    inheritance_group_id: int = Field(foreign_key="inheritance_group.id", index=True)
    product_inheritance_id: int = Field(foreign_key="product_inheritance.id", index=True)

class CategoryLink(SQLModel, table=True):
    __tablename__ = "category_link"

    id: Optional[int] = Field(default=None, primary_key=True)
    inheritance_group_id: int = Field(foreign_key="inheritance_group.id", index=True)
    category_inheritance_id: int = Field(foreign_key="category_inheritance.id", index=True)

class ProductInheritanceGroup(SQLModel, table=True):
    __tablename__ = "product_inheritance"

    id: int = Field(default=None, primary_key=True)

    #  Reference Inheritance Group
    inheritance_groups: List["InheritanceGroup"] = Relationship(back_populates="products", link_model=ProductLink)

    #Product
    product_id: int = Field(default=None, foreign_key="product.id", index=True)
    
class CategoryInheritanceGroup(SQLModel, table=True):
    __tablename__ = "category_inheritance"

    id: int = Field(default=None, primary_key=True)
    
    #  Reference Inheritance Group
    inheritance_groups: List["InheritanceGroup"] = Relationship(back_populates="categories", link_model=CategoryLink)
    
    #  Reference Category (for parent-child relationships)
    category_id: int = Field(default=None, foreign_key="category.id", index=True)

   
class InheritanceGroup(SQLModel, table=True):
    __tablename__ = "inheritance_group"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True)

    products: List["ProductInheritanceGroup"] = Relationship(back_populates="inheritance_groups", link_model=ProductLink)

    categories: List["CategoryInheritanceGroup"] = Relationship(back_populates="inheritance_groups", link_model=CategoryLink)

