from typing import Annotated
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, Depends
from db import get_session

from models.Account import User, AccessPolicy, Organization, OrganizationType, ScopeGroup, Scope, Role, ScopeGroupLink
from models.Inheritance import InheritanceGroup
from utils.model_converter_util import get_html_types
from models.Product import Product
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
            product_temp = {
                "id": product.id,
                "Product Name": product.name,
                "SKU": product.sku,
                "Description": product.description,
                "Brand": product.brand,
                "Batch Number": product.batch_number,
                "Code": product.code,
                "Price": product.price,
                "Unit": product.unit,
            }
            if product_temp not in product_list:
                product_list.append(product_temp)

        return product_list

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))    
            
# def get_products(
#     session: SessionDep, 
#     current_user: UserDep,
#     tenant: str,
# ) :
#     try:
#         if not check_permission(
#             session, "Read",  ["Administrative", "Product"], current_user
#             ):
#             raise HTTPException(
#                 status_code=403, detail="You Do not have the required privilege"
#             )
            
#         organization_ids= get_organization_ids_by_scope_group(session, current_user)

#         # Fetch categories based on organization IDs
#         db_products = session.exec(
#             select(Product).where(Product.organization_id.in_(organization_ids))
#         ).all()

#         #validate the retrived products
#         if not db_products:
#             raise HTTPException(status_code=404, detail="No products found")
        
#         Product_list = []
#         for db_product in db_products:
#             Product_temp= {
#                 "id": db_product.id,
#                 "Product Name": db_product.name,
#                 "SKU": db_product.sku,
#                 "Description": db_product.description,
#                 "Brand": db_product.brand,
#                 "Batch Number": db_product.batch_number,
#                 "Code": db_product.code,
#                 "Price": db_product.price,
#                 "Unit": db_product.unit,
#             }
#             if Product_temp not in Product_list:
#                 Product_list.append(Product_temp)
#         return Product_list
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

@pr.get("/get-product/{product_id}")            
def get_product(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    product_id: int,
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
            "batch_number": "",
            "code": "",
            "price": "",
            "unit": "",
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
    category: int = Body(...),
    organization: int = Body(...),
    sku: str = Body(...),
    name: str = Body(...),
    description: str= Body(...),
    image: str = Body(...),
    brand: str = Body(...),  
    batch_number: str = Body(...),
    code: str = Body(...),
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
            select(Product.code).where(Product.organization_id.in_(organization_ids), Product.code == code)
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
            return new_product
        
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=str(e))

@pr.put("/update-product/{product_id}") 
def update_product(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    product_id: int,

    category: int = Body(...),
    organization: int = Body(...),
    sku: str = Body(...),
    name: str = Body(...),
    description: str= Body(...),
    image: str = Body(...),
    brand: str = Body(...),  
    batch_number: str = Body(...),
    code: str = Body(...),
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
            select(Product).where(Product.organization_id.in_(organization_ids), Product.id == product_id)
        ).first()
            
        if not selected_product  :
            raise HTTPException(status_code=400, 
                                detail="Product  is not found in your organization")

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
        selected_product.category_id = category
        selected_product.organization_id = organization

        
        session.add(selected_product)
        session.commit()
        session.refresh(selected_product)

        
        return {
                "message": "Product updated successfully",
        }   
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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