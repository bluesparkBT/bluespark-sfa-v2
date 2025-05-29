from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from enum import Enum
   
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
    
class RoleLink(SQLModel, table=True):
    __tablename__ = "role_link"

    id: Optional[int] = Field(default=None, primary_key=True)
    inheritance_group_id: int = Field(foreign_key="inheritance_group.id", index=True)
    role_id: int = Field(foreign_key="role.id", index=True)

class ClassificationLink(SQLModel, table=True):
    __tablename__ = "classification_link"

    id: Optional[int] = Field(default=None, primary_key=True)
    inheritance_group_id: int = Field(foreign_key="inheritance_group.id", index=True)
    classification_id: int = Field(foreign_key="classification_group.id", index=True)  
 
class PointOfSaleLink(SQLModel, table=True):
    __tablename__ = "point_of_sale_link"

    id: Optional[int] = Field(default=None, primary_key=True)
    inheritance_group_id: int = Field(foreign_key="inheritance_group.id", index=True)
    point_of_sale_id: int = Field(foreign_key="point_of_sale.id", index=True)
    
class InheritanceGroup(SQLModel, table=True):
    __tablename__ = "inheritance_group"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    products: List["Product"] = Relationship(back_populates="inheritance_groups", link_model=ProductLink)
    categories: List["Category"] = Relationship(back_populates="inheritance_groups", link_model=CategoryLink)
    classifications: List["ClassificationGroup"] = Relationship(back_populates="inheritance_groups", link_model=ClassificationLink)
    roles: List["Role"] = Relationship(back_populates="inheritance_groups", link_model=RoleLink)
    point_of_sales: List["PointOfSale"] = Relationship(back_populates="inheritance_groups", link_model=PointOfSaleLink)
   
class Product_units(str, Enum):
    ps = "PS"
    carton = "Carton"
    kilogram = "Kilogram"
    liter = "Liter"
    packet = "Packet"
    
class Product(SQLModel, table=True):
    __tablename__ = "product"

    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(default=None)
    name: str = Field(default=None, index=True)
    description: Optional[str] = Field(default=None)
    image: Optional[str] = Field(default=None)
    brand: Optional[str] = Field(default=None, index=True)
    price: float = Field(default=None)
    unit: Product_units = Field(default=None)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id", index=True)
    category: Optional["Category"] = Relationship(back_populates="products")
    organization_id: Optional[int] = Field(default=None, foreign_key="organization.id", index=True)
    inheritance_groups: List["InheritanceGroup"] = Relationship(back_populates="products", link_model=ProductLink)


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

