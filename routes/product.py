from typing import Annotated, List, Dict, Any, Optional
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, status, Depends
from db import get_session
from utils.model_converter_util import get_html_types
from models.Product import Product, Category
from utils.util_functions import validate_name
from models.Account import User, AccessPolicy, Organization, OrganizationType, ScopeGroup, Scope, Role, ScopeGroupLink
from utils.auth_util import get_current_user, get_tenant, check_permission
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_product_id_and_name
ProductRouter = pr = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

@pr.get("/products-form")
def get_product_form(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    category: Category ,

) :
    try:
        if not check_permission(
            session, "Create", "Product", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        product_data = fetch_product_id_and_name(session)

        # product_name = product_data.get("name")

        product_name = list(product_data.values())


        form_structure = {
            "id": "",
            "sku": "",
            "name": "",
            "description": "",
            "image": "",
            "brand": "",
            "batch_number": "",
            "code": "",
            "price": "",
            "unit": "",
            "category": product_name ,
        }

        return {"data": form_structure, "html_types": get_html_types("product")}

    except Exception as e:
        # traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
            



@pr.post("/create-products")
def create_product(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    category: int = Body(...),
    organization: int = Body(...),
    sku: str = Body(...),
    name: str = Body(...),
    description: Optional[str] = Body(None),
    image: Optional[str] = Body(None),
    brand: Optional[str] = Body(None),  
    batch_number: Optional[str] = Body(None),
    code: Optional[str] = Body(None),
    price: Optional[float] = Body(None),
    unit: Optional[str] = Body(None),
):
        # Check if a product with the same SKU already exists (optional)
        try:
            # if not check_permission(
            #     session, "Create", "Product", current_user
            #     ):
            #     raise HTTPException(
            #         status_code=403, detail="You Do not have the required privilege"
            #     )
                
                # Validate SKU and Code uniqueness
            existing_product = session.exec(
                    select(Product).where(Product.sku == sku)
                ).first()
                
            if existing_product:
                raise HTTPException(status_code=400, 
                                    detail="Product  already exists")
            # Validate the name
            if not validate_name(name):
                raise HTTPException(status_code=400, detail="Invalid product name")
            if not validate_name(description):
                raise HTTPException(status_code=400, detail="Invalid product description")
            if not validate_name(brand):
                raise HTTPException(status_code=400, detail="Invalid brand name")
            if not validate_name(batch_number):
                raise HTTPException(status_code=400, detail="Invalid batch number")
            if not validate_name(code):
                raise HTTPException(status_code=400, detail="Invalid product code")
            if not validate_name(unit):
                raise HTTPException(status_code=400, detail="Invalid unit name")

            # Create a new product entry from validated input
            new_product = Product(
                                sku=sku,
                                name=name,
                                description=description,
                                image=image,
                                brand=brand,
                                batch_number=batch_number,
                                category_id=category,
                                organization_id=organization,
                                code=code,
                                price=price,
                                unit=unit,  
            )

            session.add(new_product)
            session.commit()
            session.refresh(new_product)
            return {
                    "message": "Product created successfully",
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

# Get all products
@pr.get("/get-products")
def get_products(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
) :
    try:
        if not check_permission(
            session, "Read", "Product", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        organization_ids= get_organization_ids_by_scope_group(session, current_user)

        # Fetch categories based on organization IDs
        db_products = session.exec(
            select(Product).where(Product.organization_id.in_(organization_ids))
        ).all()

        #validate the retrived products
        if not db_products:
            raise HTTPException(status_code=404, detail="No products found")
        
        Product_list = []
        for db_product in db_products:
            Product_list.append({
                "id": db_product.id,
                "Product Name": db_product.name,
                "SKU": db_product.sku,
                "Description": db_product.description,
                "Brand": db_product.brand,
                "Batch Number": db_product.batch_number,
                "Code": db_product.code,
                "Price": db_product.price,
                "Unit": db_product.unit,
            })
        return Product_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
# Get a product by ID
@pr.get("/get-product/{product_id}")            
def get_product(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    product_id: int,
) :
    try:
        if not check_permission(
            session, "Read", "Product", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
 
        # Fetch categories based on organization IDs
        db_product = session.exec(
            select(Product).where(Product.id == product_id)
        ).first()

        #validate the retrived products
        if not db_product:
            raise HTTPException(status_code=404, detail="No products found")
        
        product_list = []
        product_list.append({
            "id": db_product.id,
            "Product Name": db_product.name,
            "SKU": db_product.sku,
            "Description": db_product.description,
            "Brand": db_product.brand,
            "Batch Number": db_product.batch_number,
            "Code": db_product.code,
            "Price": db_product.price,
            "Unit": db_product.unit,
        })
        
        return product_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# Update a single product by ID
@pr.put("/update-product/{product_id}") 
def update_product(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    product_id: int,
    sku: str = Body(...),
    name: str = Body(...),
    description: Optional[str] = Body(None),
    image: Optional[str] = Body(None),
    brand: Optional[str] = Body(None),  
    batch_number: Optional[str] = Body(None),
    code: Optional[str] = Body(None),
    price: float = Body(...),
    unit: Optional[str] = Body(None),
):
    try:
        if not check_permission(
            session, "Update", "Product", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        # Validate SKU and Code uniqueness
        # selected_product = session.exec(
        #     select(Product).where(Product.id == product_id)
        # ).first()
        organization_ids= get_organization_ids_by_scope_group(session, current_user)

        # Fetch categories based on organization IDs
        selected_product = session.exec(
            select(Product).where(Product.organization_id.in_(organization_ids))
        ).first()

            
        if not selected_product  :
            raise HTTPException(status_code=400, 
                                detail="Product  is not found in your organization")
        # Validate the name
        if not validate_name(name):
            raise HTTPException(status_code=400, detail="Invalid product name")
        if not validate_name(description):
            raise HTTPException(status_code=400, detail="Invalid product description")
        if not validate_name(brand):
            raise HTTPException(status_code=400, detail="Invalid brand name")
        if not validate_name(batch_number):
            raise HTTPException(status_code=400, detail="Invalid batch number")
        if not validate_name(code):
            raise HTTPException(status_code=400, detail="Invalid product code")
        if not validate_name(unit):
            raise HTTPException(status_code=400, detail="Invalid unit name")

        # Update the product entry
     
        

        selected_product.sku = sku
        selected_product.name = name
        selected_product.description = description
        selected_product.image = image
        selected_product.brand = brand
        selected_product.batch_number = batch_number
        selected_product.code = code
        selected_product.price = price
        selected_product.unit = unit

        
        session.add(selected_product)
        session.commit()
        session.refresh(selected_product)

        
        return {
                "message": "Product updated successfully",
        }   
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
# Delete a product by ID
@pr.delete("/delete-product/{product_id}")
def delete_product(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    product_id: int,
 
) :
    try:
        if not check_permission(
            session, "Delete", "Product", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
        # Fetch categories based on organization IDs
        selected_product = session.exec(
            select(Product).where(Product.id == product_id)
        ).first()

        if not selected_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        session.delete(selected_product)
        session.commit()
        
        return {
                "message": "Product deleted successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))