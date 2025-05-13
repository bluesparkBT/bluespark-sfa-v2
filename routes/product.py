from typing import Annotated, List, Dict, Any, Optional
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from models.Product import Product, Category
from utils.util_functions import validate_name

SessionDep = Annotated[Session, Depends(get_session)]

ProductRouter = tr = APIRouter()

# Create a new category
@tr.post("/create-catagory")
def create_category(session: SessionDep, 
                    code: int = Body(...), 
                    name: str = Body(...), 
                    description: str = Body(...)) -> Category: 
    
        # Validate the name
        if not validate_name(name):
            raise HTTPException(status_code=400, detail="Invalid category name format")
        
        # Validate the description
        if not validate_name(description):
            raise HTTPException(status_code=400, detail="Invalid category description format")

        # Check if a category with the same code already exists
        # existing_category = session.query(Category).filter(Category.code == code).first()
        # existing_tenant = session.exec(select(Organization).where(Organization.organization_name == organization_name)).first()
        existing_category = session.exec(select(Category).where(Category.code == code)).first()

        if existing_category:
            raise HTTPException(status_code=400, detail="Category with this code already exists")
        # Create a new category entry from validated input
        new_category = Category(code=code, name=name, description=description)
        session.add(new_category)
        session.commit()
        session.refresh(new_category)
        return new_category

#get all categories
@tr.get("/categories")
def get_categories(session: SessionDep) -> List[Category]:
    categories = session.exec(select(Category)).all()
    
    if not categories:
        raise HTTPException(status_code=404, detail="No categories found")
    return categories


#find category by id
@tr.get("/category/{category_id}")
def get_category(category_id: int, session: SessionDep) -> Category:
    db_category = session.get(Category, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

#update category
@tr.put("/category/{category_id}")
def update_category(
    session: SessionDep,
    category_id: int,
    code: Optional[int] = Body(None),
    name: Optional[str] = Body(None),   
    description: Optional[str] = Body(None)
):
    db_category = session.get(Category, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Validate the name if provided
    if name is not None and not validate_name(name):
        raise HTTPException(status_code=400, detail="Invalid category name format")
    
    # Validate the description if provided
    if description is not None and not validate_name(description):
        raise HTTPException(status_code=400, detail="Invalid category description format")
    
    # Check if a category with the same code exists (excluding the current category)
    if code is not None:
        existing_category = session.exec(
            select(Category).where(Category.code == code, Category.id != category_id)
        ).first()
        if existing_category:
            raise HTTPException(status_code=400, detail="Category with this code already exists")
    
    # Update the category fields if provided
    if code is not None:
        db_category.code = code
    if name is not None:
        db_category.name = name
    if description is not None:
        db_category.description = description

    # Commit the changes and refresh the object
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category

#@tr.delete("/category/{category_id}")
@tr.delete("/category/{category_id}")
def delete_category(category_id: int, session: SessionDep) -> Dict[str, Any]:
    db_category = session.get(Category, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    session.delete(db_category)
    session.commit()
    return {"message": "Category deleted successfully"}

# @tr.post("/products/create", response_model=Product)
# def create_product(product: Product, session: Session = Depends(get_session)):
#     # Check if a product with the same SKU or code already exists (optional)
#     existing_product = session.query(Product).filter(
#         (Product.suk == product.suk) | (Product.code == product.code)
#     ).first()
    
#     if existing_product:
#         raise HTTPException(status_code=400, detail="Product with the same SKU or code already exists")

#     # Create a new product entry from validated input
#     new_product = Product(**product.dict())

#     session.add(new_product)
#     session.commit()
#     session.refresh(new_product)

#     return new_product





# @tr.post("/products/create", response_model=Product)
# def create_product(product: Product, session: Session = Depends(get_session)):
#     # Validate if SKU and Code are unique before insertion
#     existing_product = session.query(Product).filter(
#         (Product.suk == product.suk) | (Product.code == product.code)
#     ).first()

#     if existing_product:
#         raise HTTPException(status_code=400, detail="Product with the same SKU or code already exists")

#     # Create the new product entry with validated data
#     new_product = Product(
#         suk=product.suk,
#         name=product.name,
#         description=product.description,
#         image=product.image,
#         brand=product.brand,
#         batch_number=product.batch_number,
#         code=product.code,
#         price=product.price,
#         unit=product.unit,
#         category_id=product.category_id
#     )

#     session.add(new_product)
#     session.commit()
#     session.refresh(new_product)

#     return new_product


# @tr.get("/produt/{product_id}")
# def get_product(product_id: int ,  session: Session = Depends(get_session)):

#     db_product = session.get(Product, product_id)
#     if not db_product:
#         raise HTTPException(status_code=404, detail="product is not found")
#     if db_product:
#         return db_product


