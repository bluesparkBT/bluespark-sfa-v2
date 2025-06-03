from typing import Annotated
from db import SECRET_KEY, get_session
from sqlmodel import Session, select
from fastapi import APIRouter, HTTPException, Body, Depends
from db import get_session
from utils.model_converter_util import get_html_types
from models.Product_Category import Product, Product_units, InheritanceGroup, Category
from models.Account import Organization, ScopeGroup
from models.viewModel.ProductCategoryView import ProductView as TemplateView, UpdateProductView as UpdateTemplateView
from utils.auth_util import get_current_user, check_permission
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_category_id_and_name, fetch_organization_id_and_name
import traceback 

ProductRouter = pr = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "product"
db_model = Product

endpoint = {
    "get": f"/get-{endpoint_name}s",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",
    "update": f"/update-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}
role_modules = {   
    "get": ["Administrative", "Product"],
    "get_form": ["Administrative", "Product"],
    "create": ["Administrative", "Product"],
    "update": ["Administrative", "Product"],
    "delete": ["Administrative", "Product"],
}


@pr.get(endpoint['get'])
def get_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str

):
    try:
        if not check_permission(
            session, "Read",role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        inherited_group_id = session.exec(
            select(Organization.inheritance_group).where(Organization.id == current_user.organization)
        ).first()

        inherited_group = session.exec(
            select(InheritanceGroup).where(InheritanceGroup.id == inherited_group_id)
        ).first()

        if inherited_group:
            inherited_product = inherited_group.product
        else:
            inherited_product = []
        
        scope_group = session.exec(select(ScopeGroup).where(ScopeGroup.id == current_user.scope_group)).first()
   
        if scope_group != None:
            existing_orgs = [organization.id for organization in scope_group.organizations ]
        if scope_group == None:
            existing_orgs= []

        organization_product = session.exec(
            select(db_model).where(db_model.organization.in_(existing_orgs))
        ).all()
        organization_product.extend(inherited_product)

        product_list = []
        for product in organization_product:
            product_category = session.exec(select(Category).where(Category.id == product.category_id)).first()
            product_temp = {
                "Product Name": product.name,
                "SKU": product.sku,
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
      
@pr.get(endpoint['get_form'])
def get_template_form(
    tenant: str,
    session: SessionDep,
    current_user: UserDep,
) :
    try:
        if not check_permission(
            session, "Create",role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
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

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")

@pr.post(endpoint['create'])
def create_product(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    valid: TemplateView,
):
    try:
        if not check_permission(
            session, "Create",role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

            # Validate SKU and Code uniqueness
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        selected_product = session.exec(
            select(db_model)
            .where(db_model.organization.in_(organization_ids), db_model.name == valid.name, db_model.sku == valid.sku)
            ).first()
        if selected_product:
            raise HTTPException(status_code=400, 
                                detail="Product  already exists")
        
        # Create a new product entry from validated input
        new_entry = db_model.model_validate(valid)
        session.add(new_entry)
        session.commit()
        session.refresh(new_entry)

        return new_entry

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
   
@pr.put(endpoint['update'])
def update_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    valid: UpdateTemplateView,
):
    try:
        if not check_permission(
            session, "Update",role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        selected_product = session.exec(
            select(db_model).where(db_model.organization.in_(organization_ids), db_model.id == valid.id)
        ).first()
            
        if not selected_product  :
            raise HTTPException(status_code=400, 
                                detail= f"{endpoint_name} is not found.")
        selected_product.sku = valid.sku
        selected_product.name = valid.name
        if valid.description:
            selected_product.description = valid.description
        if valid.image:
            selected_product.image = valid.image
        selected_product.brand = valid.brand
        selected_product.price = valid.price
        selected_product.unit = valid.unit
        selected_product.category_id = valid.category_id
        selected_product.organization = valid.organization

        
        session.add(selected_product)
        session.commit()
        session.refresh(selected_product)

        
        return {"message": "Product updated successfully"}   
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    

@pr.delete(endpoint['delete']+ "/{id}")
def delete_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int
)  :
    try:
        if not check_permission(
            session, "Delete",role_modules['delete'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        selected_product = session.exec(
            select(Product).where(Product.id == id)
        ).first()

        if not selected_product:
            raise HTTPException(status_code=404, detail= f"{endpoint_name} not found")
        
        session.delete(selected_product)
        session.commit()
        
        return {"message": f"{endpoint_name} deleted successfully"}
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
    