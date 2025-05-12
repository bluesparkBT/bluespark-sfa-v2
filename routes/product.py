from typing import Annotated, List, Dict, Any, Optional
from db import SECRET_KEY, get_session
from sqlmodel import Session
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from models.Product import Product, Category

SessionDep = Annotated[Session, Depends(get_session)]

ProductRouter = tr = APIRouter()

# async def create_category(category: Category, session: Session = Depends(get_session)):
#     new_category = Category(code= code, name=name, description=description)
#     session.add(new_category)
#     session.commit()
#     session.refresh(new_category)
#     return new_category
@tr.post("/create/catagory")
def create_category(session: SessionDep, code: int = Body(...), name: str = Body(...), description: str = Body(...)) -> Category:
    new_category = Category(code=code, name=name, description=description)
    session.add(new_category)
    session.commit()
    session.refresh(new_category)
    return new_category

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


