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
        return ["point_of_sale"]
    elif endpoint == "Organization":
        return ["scope_groups"]
    else:
        return []
