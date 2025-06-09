from sqlmodel import select
from fastapi import Request, HTTPException, status, Depends
from typing import Annotated
from db import  get_session
from models.Account import (Organization, User, Role, ScopeGroup, ScopeGroupLink)
from models.Address import Address, Geolocation
from models.Product_Category import Category, Product, InheritanceGroup, ProductLink, CategoryLink
from models.Marketing import ClassificationGroup, CustomerDiscount
from models.PointOfSale import PointOfSale, Outlet, WalkInCustomer
from models.RoutesAndVisits import Route, Territory
#from models.Warehouse import Stock, StockType, Warehouse, Vehicle
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.auth_util import get_current_user
from sqlmodel import Session, select

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


def fetch_id_and_name(session: Session, current_user: User, model_class: type):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    stmt = select(model_class.id, model_class.name).where(
        getattr(model_class, "organization").in_(organization_ids)
    )
    rows = session.exec(stmt).all()
    return {row[0]: row[1] for row in rows}

def fetch_user_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)
    users_row = session.exec(
        select(User.id, User.username).where(User.organization.in_(organization_ids))
    ).all()
    
    users = {row[0]: row[1] for row in users_row}
    return users

def fetch_organization_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    organization_rows = session.exec(
        select(Organization.id, Organization.name)
        .where(Organization.id.in_(organization_ids))
    ).all()

    organizations = {row[0]: row[1] for row in organization_rows}
    return organizations
def fetch_organization_ids(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    organization_rows = session.exec(
        select(Organization.id)
        .where(Organization.id.in_(organization_ids))
    ).all()

    # Extract only the IDs from the result rows (each row is a one-item tuple)
    organization_ids_list = [row[0] for row in organization_rows]
    return organization_ids_list

def fetch_route_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    route_rows = session.exec(
        select(Route.id, Route.name)
        .where(Route.id.in_(organization_ids))
    ).all()
    routes = {row[0]: row[1] for row in route_rows}
    return routes
  
def fetch_territory_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    territory_rows = session.exec(
        select(Territory.id, Territory.name)
        .where(Territory.id.in_(organization_ids))
    ).all()

    territorys = {row[0]: row[1] for row in territory_rows}
    return territorys 
   
def fetch_discount_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    discount_rows = session.exec(
        select(CustomerDiscount.id)
        # .where(CustomerDiscount.organization.in_(organization_ids))
    ).all()

    # Ensure the function returns only a list of IDs
    discount_ids = [row for row in discount_rows if row is not None]

    return discount_ids




# def fetch_discount_id_and_name(session: SessionDep, current_user: UserDep):
#     organization_ids = get_organization_ids_by_scope_group(session, current_user)

#     discount_rows = session.exec(
#         select(CustomerDiscount.id, CustomerDiscount.name)
#         .where(CustomerDiscount.id.in_(organization_ids))
#     ).all()

#     discounts = {row[0]: row[1] for row in discount_rows}
#     return discounts 
# def fetch_role_id_and_name(session: SessionDep, current_user: UserDep):
#     organization_ids = get_organization_ids_by_scope_group(session, current_user)

#     role_rows = session.exec(
#         select(Role.id, Role.name)
#         .where(Role.organization.in_(organization_ids))
#     ).all()

#     roles = {row[0]: row[1] for row in role_rows}
#     return roles

def fetch_outlet_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    outlet_rows = session.exec(
        select(Outlet.id, Outlet.name)
        .where(Outlet.organization.in_(organization_ids))
    ).all()

    outlets = {row[0]: row[1] for row in outlet_rows}
    return outlets

def fetch_wakl_in_customer_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    wakl_in_customer_rows = session.exec(
        select(WalkInCustomer.id, WalkInCustomer.name)
        .where(WalkInCustomer.organization.in_(organization_ids))
    ).all()

    wakl_in_customers = {row[0]: row[1] for row in wakl_in_customer_rows }
    return wakl_in_customers

def fetch_role_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    role_rows = session.exec(
        select(Role.id, Role.name)
        .where(Role.organization.in_(organization_ids))
    ).all()

    roles = {row[0]: row[1] for row in role_rows}
    return roles

def fetch_scope_group_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    scope_group_row = session.exec(
        select(ScopeGroup.id, ScopeGroup.name)
        .where(ScopeGroup.tenant_id.in_(organization_ids))
        ).all()
    scope_groups = {row[0]: row[1] for row in scope_group_row}
    return scope_groups

# def fetch_scope_group_id_and_name(session: SessionDep, current_user: UserDep):
#     organization_ids = get_organization_ids_by_scope_group(session, current_user)
#     print("organizations::::", organization_ids)
#     scope_group_rows = session.exec(
#         select(ScopeGroup.id, ScopeGroup.name)
#         .join(ScopeGroupLink, ScopeGroup.id == ScopeGroupLink.scope_group)
#         .where(ScopeGroupLink.organization.in_(organization_ids))
#         .distinct()
#     ).all()

#     # Convert to dictionary: {id: name}
#     scope_groups = {row[0]: row[1] for row in scope_group_rows}
#     return scope_groups


def fetch_product_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    product_row = session.exec(
        select(Product.id, Product.name)
        .where(Product.organization.in_(organization_ids))
        ).all()
    products = {row[0]: row[1] for row in product_row}
    return products

def fetch_category_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    category_row = session.exec(
        select(Category.id, Category.name)
        .where(Category.organization.in_(organization_ids))
        ).all()
    categories = {row[0]: row[1] for row in category_row}
    return categories

def fetch_inheritance_group_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    inheritance_row = session.exec(
        select(InheritanceGroup.id, InheritanceGroup.name)
        .where(InheritanceGroup.organization.in_(organization_ids))
        ).all()
    inheritance_groups = {row[0]: row[1] for row in inheritance_row}
    return inheritance_groups

# def fetch_inheritance_group_id_and_name(session: SessionDep, current_user: UserDep):
#     organization_ids = get_organization_ids_by_scope_group(session, current_user)

#     # Step 2: Get distinct inheritance_group IDs from those organizations
#     inheritance_group_ids = session.exec(
#         select(Organization.inheritance_group)
#         .where(Organization.id.in_(organization_ids))
#         .where(Organization.inheritance_group.is_not(None))
#     ).all()

#     # Step 3: Use those IDs to get inheritance group names
#     if not inheritance_group_ids:
#         return {}

#     inheritance_groups = session.exec(
#         select(InheritanceGroup.id, InheritanceGroup.name)
#         .where(InheritanceGroup.id.in_(inheritance_group_ids))
#     ).all()

#     return {row[0]: row[1] for row in inheritance_groups}

def fetch_address_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    address_row = session.exec(
        select(Address.id, Address.sub_city)
        .where(Address.organization.in_(organization_ids))
        ).all()
    products = {row[0]: row[1] for row in address_row}
    return products

def fetch_geolocation_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    address_row = session.exec(
        select(Geolocation.id, Geolocation.name)
        .where(Geolocation.organization.in_(organization_ids))
        ).all()
    products = {row[0]: row[1] for row in address_row}
    return products

def fetch_classification_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    classification_row = session.exec(
        select(ClassificationGroup.id, ClassificationGroup.name)
        .where(ClassificationGroup.organization.in_(organization_ids))
    ).all()

    classifications = {row[0]: row[1] for row in classification_row if row[0] is not None}
    return classifications

# def fetch_customer_discount_id_and_name(session: SessionDep, current_user: UserDep):
#     organization_ids = get_organization_ids_by_scope_group(session, current_user)

#     classification_row = session.exec(
#         select(CustomerDiscount.id, CustomerDiscount.discount)).all()
#         # .where(CustomerDiscount.organization.in_(organization_ids))
#     # ).all()
#     print(classification_row)
#     # customer_discount = {row[0]: str(row[1]) for row in classification_row if row[0] is not None}
#     customer_discount = {row[0]: row[1] for row in classification_row if row[0] is not None}
#     print(customer_discount)

#     return customer_discount
def fetch_point_of_sale_ids(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)
    pos_rows = session.exec(select(PointOfSale.id).where(PointOfSale.organization.in_(organization_ids))).all()
    
    # Ensure extracted values are clean integers
    point_of_sale_ids = [row for row in pos_rows if row is not None]
    
    return point_of_sale_ids


# def fetch_point_of_sale_id_and_name(session: SessionDep, current_user: UserDep):
#     organization_ids = get_organization_ids_by_scope_group(session, current_user)

#     pos_row = session.exec(
#         select(PointOfSale.id)
#         .where(PointOfSale.organization.in_(organization_ids))
#     ).all()

#     pos = {row[0]: row[1] for row in pos_row if row[0] is not None}
#     return pos 

def fetch_outlet_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)
    outlet_row = session.exec(
        select(Outlet.id, Outlet.name)
        .where(PointOfSale.organization.in_(organization_ids))
        ).all()
    outlet = {row[0]: row[1] for row in outlet_row}
    return outlet 

# def fetch_warehouse_id_and_name(session: SessionDep, current_user: UserDep):
#     organization_ids = get_organization_ids_by_scope_group(session, current_user)

#     warehouse_row = session.exec(
#         select(Warehouse.id, Warehouse.warehouse_name)
#         .where(Warehouse.organization.in_(organization_ids))
#         ).all()
#     warehouses = {row[0]: row[1] for row in warehouse_row}
#     return warehouses

# def fetch_stocks_id_and_name(session: SessionDep, current_user: UserDep):
#     organization_ids = get_organization_ids_by_scope_group(session, current_user)
#     stock_row = session.exec(
#         select(Stock.id, Stock.stock_type, Product.name)
#         .join(Warehouse, Warehouse.id == Stock.warehouse_id)
#         .join(Product, Product.id == Stock.product_id)
#         .where(Warehouse.organization.in_(organization_ids))
#     ).all()

#     print(stock_row)

#     stocks = {
#         row[0] :row[2] + convert_promotional(row[1])
#         for row in stock_row
#     }
#     return stocks

# def fetch_vehicle_id_and_name(session: SessionDep, current_user: UserDep):
#     organization_ids = get_organization_ids_by_scope_group(session, current_user)

#     vehicle_row = session.exec(
#         select(Vehicle.id, Vehicle.name)
#         .where(Vehicle.organization.in_(organization_ids))
#         ).all()
#     vehicles = {row[0]: row[1] for row in vehicle_row}
#     return vehicles


def add_category_link(session: SessionDep, inheritance_group_id: int, category_id: int):

# Check if the link already exists to prevent duplicates
    existing_link = session.exec(
        select(CategoryLink).where(
            CategoryLink.inheritance_group_id == inheritance_group_id,
            CategoryLink.category_id == category_id
        )
    ).first()

    if existing_link:
        return {"message": "Category already linked to inheritance group"}

    # Create new category link
    new_link = CategoryLink(
        inheritance_group_id=inheritance_group_id,
        category_id=category_id
    )

    session.add(new_link)
    session.commit()
    session.refresh(new_link)

    return {"message": "Category linked successfully", "link": new_link}

def add_product_link(session: SessionDep, inheritance_group_id: int, product_id: int):

# Check if the link already exists to prevent duplicates
    existing_link = session.exec(
        select(ProductLink).where(
            ProductLink.inheritance_group_id == inheritance_group_id,
            ProductLink.product_id == product_id
        )
    ).first()

    if existing_link:
        return {"message": "product already linked to inheritance group"}

    # Create new category link
    new_link = ProductLink(
        inheritance_group_id=inheritance_group_id,
        product_id=product_id
    )

    session.add(new_link)
    session.commit()
    session.refresh(new_link)

    return {"message": "product linked successfully", "link": new_link}
    
def get_user_inheritance_group(session, current_user):
    """
    Retrieves the inheritance group associated with the current user's organization.

    Args:
        session: SQLModel session instance.
        current_user: User instance with an organization.

    Returns:
        inherited_group: The InheritanceGroup object if found, otherwise None.
        inherited_products: List of inherited products if the group exists, otherwise an empty list.
    """
    inherited_group_id = session.exec(
        select(Organization.inheritance_group).where(
            Organization.id == current_user.organization
        )
    ).first()

    if not inherited_group_id:
        return None, []

    inherited_group = session.exec(
        select(InheritanceGroup).where(InheritanceGroup.id == inherited_group_id)
    ).first()

    if inherited_group:
        return inherited_group, inherited_group.product
    return None, []
