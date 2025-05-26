from sqlmodel import select
from fastapi import Request, HTTPException, status, Depends
from typing import Annotated
from db import  get_session
from models.Account import (
    Organization,
    User,
    Role,
    ScopeGroup
)
from models.Address import Address, Geolocation
from models.Product import Category, Product
from models.Inheritance import InheritanceGroup, ProductLink, CategoryLink
from models.Warehouse import Stock, StockType, Warehouse, Vehicle, WarehouseGroup, WarehouseGroupLink, WarehouseStoreAdminLink
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.auth_util import get_current_user
from sqlmodel import Session, select

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


def fetch_user_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)
    
    users_row = session.exec(
        select(User.id, User.fullname).where(User.organization_id.in_(organization_ids))
    ).all()
    
    users = {row[0]: row[1] for row in users_row}
    return users

def fetch_organization_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    organization_rows = session.exec(
        select(Organization.id, Organization.organization_name)
        .where(Organization.id.in_(organization_ids))
    ).all()

    organizations = {row[0]: row[1] for row in organization_rows}
    return organizations

def fetch_role_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    role_rows = session.exec(
        select(Role.id, Role.name)
        .where(Role.organization_id.in_(organization_ids))
    ).all()

    roles = {row[0]: row[1] for row in role_rows}
    return roles

def fetch_scope_group_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)
    print("fetched organizations", organization_ids)

    scope_group_row = session.exec(
        select(ScopeGroup.id, ScopeGroup.scope_name)
        .where(ScopeGroup.parent_id.in_(organization_ids))
        ).all()
    scope_groups = {row[0]: row[1] for row in scope_group_row}
    return scope_groups


def fetch_product_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    product_row = session.exec(
        select(Product.id, Product.name)
        .where(Role.organization_id.in_(organization_ids))
        ).all()
    products = {row[0]: row[1] for row in product_row}
    return products

def fetch_category_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    category_row = session.exec(
        select(Category.id, Category.name)
        .where(Category.organization_id.in_(organization_ids))
        ).all()
    categories = {row[0]: row[1] for row in category_row}
    return categories

def fetch_inheritance_group_id_and_name(session: SessionDep, current_user: UserDep):
    # Step 1: Get the list of organization IDs the current user has access to
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    # Step 2: Get distinct inheritance_group IDs from those organizations
    inheritance_group_ids = session.exec(
        select(Organization.inheritance_group)
        .where(Organization.id.in_(organization_ids))
        .where(Organization.inheritance_group.is_not(None))
    ).all()

    # Step 3: Use those IDs to get inheritance group names
    if not inheritance_group_ids:
        return {}

    inheritance_groups = session.exec(
        select(InheritanceGroup.id, InheritanceGroup.name)
        .where(InheritanceGroup.id.in_(inheritance_group_ids))
    ).all()

    return {row[0]: row[1] for row in inheritance_groups}

def fetch_address_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    address_ids = session.exec(
        select(Organization.address_id)
        .where(Organization.id.in_(organization_ids))
    ).all()
    
    address_ids = [
        aid[0] for aid in address_ids if aid is not None and aid[0] is not None
    ] 
    if not address_ids:
        return {}

    address_row = session.exec(
        select(Address.id, Address.name)
        .where(Address.id.in_(address_ids))
    ).all()

    return {row[0]: row[1] for row in address_row}


def fetch_admin_warehouse_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    warehouse_row = session.exec(
        select(Warehouse.id, Warehouse.warehouse_name)
        .where(Warehouse.organization_id.in_(organization_ids))
        .distinct()
    ).all()
    warehouses = {row[0]: row[1] for row in warehouse_row}
    return warehouses

def fetch_warehouse_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    warehouse_row = session.exec(
        select(Warehouse.id, Warehouse.warehouse_name)
        .join(WarehouseGroupLink, WarehouseGroupLink.warehouse_id == Warehouse.id)
        .join(WarehouseStoreAdminLink, WarehouseStoreAdminLink.warehouse_group_id == WarehouseGroupLink.warehouse_group_id)
        .where(WarehouseStoreAdminLink.user_id == current_user.id)  
        .where(Warehouse.organization_id.in_(organization_ids))
        .distinct()
    ).all()
    warehouses = {row[0]: row[1] for row in warehouse_row}
    return warehouses

def fetch_stocks_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)
    stock_row = session.exec(
        select(Stock.id, Stock.stock_type, Product.name)
        .join(Warehouse, Warehouse.id == Stock.warehouse_id)
        .join(Product, Product.id == Stock.product_id)
        .join(WarehouseGroupLink, WarehouseGroupLink.warehouse_id == Warehouse.id)
        .join(WarehouseStoreAdminLink, WarehouseStoreAdminLink.warehouse_group_id == WarehouseGroupLink.warehouse_group_id)
        .where(WarehouseStoreAdminLink.user_id == current_user.id) 
        .where(Warehouse.organization_id.in_(organization_ids)).distinct()
    ).all()

    print(stock_row)

    stocks = {
        row[0] :row[2] + convert_promotional(row[1])
        for row in stock_row
    }
    return stocks

def fetch_vehicle_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    vehicle_row = session.exec(
        select(Vehicle.id, Vehicle.name)
        .where(Vehicle.organization_id.in_(organization_ids))
        ).all()
    vehicles = {row[0]: row[1] for row in vehicle_row}
    return vehicles


def convert_promotional(stock_type: StockType):
    if stock_type == StockType.promotional:
        return "(Promotional)"
    else:
        return ""
    
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

def fetch_warehouse_group_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)
    group_row = session.exec(
        select(WarehouseGroup.id, WarehouseGroup.name).where(WarehouseGroup.organization_id.in_(organization_ids))
    ).all()

    print(group_row)

    groups = {
        row[0] :row[1]
        for row in group_row
    }
    return groups
