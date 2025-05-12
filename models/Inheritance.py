from sqlmodel import SQLModel, Field, Relationship
from enum import Enum   
from typing import Optional, List
from models.Product import Product, Category


class ProductInheritanceGroup(SQLModel, table=True):
    __tablename__ = "productinheritance"

    id: int = Field(default=None, primary_key=True)
    
    #  Reference Inheritance Group
    inheritance_group: int = Field(default=None, foreign_key="inheritancegroup.id", index=True)
    
    #  Reference Product (for parent-child relationships)
    product_id: int = Field(default=None, foreign_key="product.id", index=True)

    product: "Product" = Relationship(back_populates="products")




class CategoryInheritanceGroup(SQLModel, table=True):
    __tablename__ = "categoryinheritance"

    id: int = Field(default=None, primary_key=True)
    
    #  Reference Inheritance Group
    inheritance_group: int = Field(default=None, foreign_key="inheritancegroup.id", index=True)
    
    #  Reference Category (for parent-child relationships)
    category_id: int = Field(default=None, foreign_key="category.id", index=True)
   
    category: "Category" = Relationship(back_populates="categories")

class InheritanceGroup(SQLModel, table=True):
    __tablename__ = "inheritancegroup"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True)

    products: List["ProductInheritanceGroup"] = Relationship(back_populates="inheritance_group")

    categories: List["CategoryInheritanceGroup"] = Relationship(back_populates="inheritance_group")

