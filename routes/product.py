from typing import Annotated
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, Depends
from db import get_session
from utils.model_converter_util import get_html_types
from models.Product_Category import Product, Product_units, InheritanceGroup, Category
from models.Account import Organization, ScopeGroup
from utils.util_functions import validate_name
from utils.auth_util import get_current_user, check_permission
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_category_id_and_name, fetch_organization_id_and_name
import traceback 
ProductRouter = pr = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

@pr.get("/get-products")
def get_products(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
) :
    try:
        if not check_permission(
            session, "Read",  ["Administrative", "Product"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        inherited_group_id = session.exec(
            select(Organization.inheritance_group).where(Organization.id == current_user.organization_id)
        ).first()

        inherited_group = session.exec(
            select(InheritanceGroup).where(InheritanceGroup.id == inherited_group_id)
        ).first()

        if inherited_group:
            inherited_product = inherited_group.product
        else:
            inherited_product = []
        
        scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == current_user.scope_group_id)).first()
   
        if scope_group != None:
            existing_orgs = [organization.id for organization in scope_group.organizations ]
        if scope_group == None:
            existing_orgs= []

        organization_product = session.exec(
            select(Product).where(Product.organization_id.in_(existing_orgs))
        ).all()
        organization_product.extend(inherited_product)

        product_list = []
        for product in organization_product:
            product_category = session.exec(select(Category).where(Category.id == product.category_id)).first()
            product_temp = {
                "id": product.id,
                "Product Name": product.name,
                "SKU": product.sku,
                "description": product.description,
                "Brand": product.brand,
                "Price": product.price,
                "Unit": product.unit,
                "Category": product_category.name if product_category else "N/A",
            }
            if product_temp not in product_list:
                product_list.append(product_temp)

        return product_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))    

@pr.get("/get-product/{id}")            
def get_product(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int,
) :
    try:
        if not check_permission(
            session, "Read", ["Administrative","Product"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            
 
        # Fetch categories based on organization IDs
        db_product = session.exec(
            select(Product).where(Product.id == id)
        ).first()

        #validate the retrived products
        if not db_product:
            raise HTTPException(status_code=404, detail="No products found")
        
        product_list = []
        product_list.append({
            "id": db_product.id,
            "Product Name": db_product.name,
            "SKU": db_product.sku,
            "description": db_product.description,
            "Brand": db_product.brand,
            "Price": db_product.price,
            "Unit": db_product.unit,
        })
        
        return product_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
      
@pr.get("/product-form")
def get_product_form(
    tenant: str,
    session: SessionDep, 
    current_user: UserDep,
) :
    try:
        # Check permission
        if not check_permission(
            session, "Read",["Administrative", "Product"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )  
        
        # product_data = fetch_product_id_and_name(session)

        # # product_name = product_data.get("name")

        # product_name = list(product_data.values())


        form_structure = {
            "id": "",
            "sku": "",
            "name": "",
            "description": "",
            "image": "",
            "brand": "",
            "price": "",
            "unit": {i.value: i.value for i in Product_units},
            "category": fetch_category_id_and_name(session, current_user) ,
            "organization": fetch_organization_id_and_name(session, current_user),

        }

        return {"data": form_structure, "html_types": get_html_types("product")}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
            
@pr.post("/create-product")
def create_product(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    category_id: int = Body(...),
    organization: int = Body(...),
    sku: str = Body(...),
    name: str = Body(...),
    description: str= Body(...),
    image: str = Body(...),
    brand: str = Body(...),  
    price: float = Body(...),
    unit: str = Body(...)
):
    try:
        if not check_permission(
            session, "Create",["Administrative", "Product"], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )  
            
            # Validate SKU and Code uniqueness
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        db_category_code = session.exec(
            select(Product)
            .where(Product.organization_id.in_(organization_ids), Product.name == name, Product.sku == sku)
            ).first()
        if db_category_code:
            raise HTTPException(status_code=400, 
                                detail="Product  already exists")
        # Validate the name
        if not validate_name(name):
            raise HTTPException(status_code=400, detail="Invalid product name")
        

        # Create a new product entry from validated input
        new_product = Product(        
            sku=sku,
            name=name,
            description=description,
            image=image,
            brand=brand,
            category_id=category_id,
            organization_id=organization,
            price=price,
            unit=unit,  
        )

        session.add(new_product)
        session.commit()
        session.refresh(new_product)
        return new_product
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@pr.put("/update-product/") 
def update_product(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    
    id: int = Body(...),
    category: int = Body(...),
    organization: int = Body(...),
    sku: str = Body(...),
    name: str = Body(...),
    description: str= Body(...),
    image: str = Body(...),
    brand: str = Body(...),  
    price: float = Body(...),
    unit: str = Body(...)
):
    try:
        if not check_permission(
            session, "Update", "Product", current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
            

        # Fetch categories based on organization IDs
        organization_ids = get_organization_ids_by_scope_group(session, current_user)

        selected_product = session.exec(
            select(Product).where(Product.organization_id.in_(organization_ids), Product.id == id)
        ).first()
            
        if not selected_product  :
            raise HTTPException(status_code=400, 
                                detail="Product is not found.")
        # Update the product entry
        selected_product.sku = sku
        selected_product.name = name
        if description:
            selected_product.description = description
        if image:
            selected_product.image = image
        selected_product.brand = brand
        selected_product.price = price
        selected_product.unit = unit
        selected_product.category_id = category
        selected_product.organization_id = organization

        
        session.add(selected_product)
        session.commit()
        session.refresh(selected_product)

        
        return {
                "message": "Product updated successfully",
        }   
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@pr.delete("/delete-product/{id}")
def delete_product(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int,
 
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
            select(Product).where(Product.id == id)
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