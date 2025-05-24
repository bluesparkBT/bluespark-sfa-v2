from typing import Annotated
from fastapi import APIRouter, Depends

from utils.auth_util import get_current_user


UtilRouter = ur = APIRouter()

endpoint = "Util"
UserDep = Annotated[dict, Depends(get_current_user)]


@ur.get("/hidden-table-fields")
async def get_form_fields_warehouse(current_user: UserDep, endpoint: str) -> list[str]:
    """
    Get the hidden table fields for the warehouse.

    Endpoints that currently have hidden table fields:
    - Outlet
    - WalkInCustomer

    """
    if endpoint == "Outlet":
        return [
            "company_name",
            "outlet_name",
            "channel",
            "tin",
            "phone",
            "email",
            "country",
            "city",
            "sub_city",
            "woreda",
            "landmark",
            "latitude",
            "longitude",
        ]
    elif endpoint == "Walk-in Customer":
        return [
            "id",
            "point_of_sale"]
    elif endpoint == "Organization":
        return [
            "id",
            "description",
            "organization_type",
            "inheritance_group",
            "scope_groups"]
    elif endpoint == "Users":
        return ["id",
                "scope_group_id",
                "manager",
                "phone_number",
                "scope",
                "scope_group"
                ]
    elif endpoint == "Role":
        return ["id"]
    elif endpoint == "Category":
        return ["id",
                "description"]
    elif endpoint == "Product":
        return ["id",
                "description"]
    elif endpoint == "Inheritance":
        return ["id"]
    elif endpoint == "Address":
        return ["id"]
    elif endpoint == "Scope Group":
        return ["id"]
    elif endpoint == "Route":
        return ["id",
                "description"]
    elif endpoint == "Route Schedule":
        return ["id",
                "description"]
    elif endpoint == "Sales":
        return ["id"]
    elif endpoint == "Penetration":
        return ["id"]
    elif endpoint == "Sales Activation":
        return ["id"]
    elif endpoint == "Classification":
        return ["id",
                "description"]
    elif endpoint == "Stock":
        return ["id"]
    elif endpoint == "Tenant":
        return ["id",
                "description"]
    elif endpoint == "Territory":
        return ["id",
                "description"]
    elif endpoint == "Travel":
        return ["id"]
    elif endpoint == "Vehicle":
        return ["id"]
    elif endpoint == "Complaint":
        return ["id"]
    elif endpoint == "Deposit":
        return ["id"]
    elif endpoint == "Warehouse":
        return ["id" ]
    elif endpoint == "Warehouse Stop":
        return [
            "id",
            "confirmed"]
    else:
        return []
