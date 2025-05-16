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
from models.Product import Category, Product
from models.Inheritance import InheritanceGroup
from models.Inventory_Management import Stock, Warehouse
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

    scope_group_row = session.exec(
        select(ScopeGroup.id, ScopeGroup.scope_name)
        .where(Role.organization_id.in_(organization_ids))
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
        .where(Role.organization_id.in_(organization_ids))
        ).all()
    categories = {row[0]: row[1] for row in category_row}
    return categories

def fetch_inheritance_group_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    inheritance_group_row = session.exec(
        select(InheritanceGroup.id, InheritanceGroup.name)
        .where(Role.organization_id.in_(organization_ids))
        ).all()
    inheritance_groups = {row[0]: row[1] for row in inheritance_group_row}
    return inheritance_groups

def fetch_warehouse_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    warehouse_row = session.exec(
        select(Warehouse.id, Warehouse.name)
        .where(Warehouse.organization_id.in_(organization_ids))
        ).all()
    warehouses = {row[0]: row[1] for row in warehouse_row}
    return warehouses

def fetch_stocks_id_and_name(session: SessionDep, current_user: UserDep):
    organization_ids = get_organization_ids_by_scope_group(session, current_user)

    stock_row = session.exec(
        select(Stock.id, Stock.name)
        .where(Stock.organization_id.in_(organization_ids))
        ).all()
    stocks = {
        row.id: row.product_virtual.name + convert_promotional(row.is_promotional)
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


def convert_promotional(promo: bool):
    if promo:
        return " Promotional"
    else:
        return ""
