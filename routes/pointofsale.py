import traceback
from datetime import datetime
from fastapi import Depends, HTTPException, Body, APIRouter
from typing import Annotated, Optional
from fastapi.routing import APIRouter
from sqlmodel import and_, select, Session
from db import get_session
from models.PointOfSale import PointOfSale, Outlet, WalkInCustomer,ChannelType, POSStatus
from models.Utils import ErrorLog
from utils.address_util import check_address
from utils.auth_util import get_current_user
from models.viewModel.pointOfSaleView import PointOfSaleView as TemplateView , UpdatePointOfSaleView as TemplateViews

from utils.model_converter_util import get_html_types
from utils.auth_util import check_permission, check_permission_and_scope
from utils.form_db_fetch import( get_organization_ids_by_scope_group,
                                fetch_organization_ids,
                                fetch_wakl_in_customer_id_and_name,
                                fetch_outlet_id_and_name,
                                fetch_territory_id_and_name,
                                fetch_route_id_and_name
                                ) 

# Update router name
PointOfSaleRouter = c = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "point-of-sale"  # Update this
db_model = PointOfSale  # Update this

endpoint = {
    "get": f"/get-{endpoint_name}",
    "get_by_id": f"/get-{endpoint_name}/{{id}}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",
    "update": f"/update-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}

# Update role_modules
role_modules = {
    "get": ["Administrative"],
    "get_form": ["Administrative"],
    "create": ["Administrative"],
    "update": ["Administrative"],
    "delete": ["Administrative"],
}

# CRUD Operations

@c.get(endpoint['get'])
def get_point_of_sales(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:
        orgs_in_scope = check_permission_and_scope(session, "Read", role_modules['get'], current_user)

        entries_list = session.exec(
            select(db_model).where(db_model.organization.in_(orgs_in_scope["organization_ids"]))
        ).all()

        return entries_list

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")


@c.get(endpoint['get_by_id'])
def get_point_of_sale_by_id(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int
):
    try:
        if not check_permission(session, "Read", role_modules['get'], current_user):
            raise HTTPException(status_code=403, detail="You do not have the required privilege")

        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        entry = session.exec(
            select(db_model).where(db_model.organization.in_(organization_ids), db_model.id == id)
        ).first()

        if not entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

        return entry

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")



@c.get (endpoint['get_form'])
def pointofsale_form(
    tenant: str,
    session: SessionDep,
    current_user: UserDep,   
):
    try:
        if not check_permission(
            session, "Create",role_modules['get_form'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        form_data = {
            "id": "",
            "outlet_name": "",
            "channel": [channel.value for channel in ChannelType],
            "tin": "",
            "phone": "",
            "outlet_email": "",
            "latitude": "",
            "longitude": "",

            "customer_id": "",     
            "customer_name": "",
            "customer_email": "",
            "route": fetch_route_id_and_name(session,current_user),
            "territoy": fetch_territory_id_and_name(session, current_user ),
            # "outlet_id": fetch_outlet_id_and_name(session,current_user),
      } 

        return {"tabs": {"outlet":["id","outlet_name","channel","tin","phone","outlet_email","latitude","longitude"],
                        "walk_in_customer":["customer_id", "customer_name","customer_email","route","territoy"]
        },
            "data": form_data, "html_types": get_html_types("point_of_sale")}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))




# @c.post(endpoint['create'])
# def create_point_of_sale(
#     session: SessionDep,
#     tenant: str,
#     current_user: UserDep,
#     valid: TemplateView
# ):
#     try:
#         if not check_permission(session, "Create", role_modules['create'], current_user):
#             raise HTTPException(status_code=403, detail="You do not have the required privilege")

#         # new_entry = db_model.model_validate(valid)
#         def parse_float(val):
#             if val == "":
#                 return None
#             if isinstance(val, float):
#                 return val
#             try:
#                 return float(val)
#             except (TypeError, ValueError):
#                 raise HTTPException(status_code=400, detail="Latitude/Longitude must be a float or null.")
        
#         outlet= Outlet(
#             name = valid.outlet_name,
#             channel=valid.channel,
#             tin = valid.tin ,
#             phone = valid.phone ,
#             email = valid.outlet_email,

#         latitude = parse_float(valid.latitude),
#         longitude = parse_float(valid.longitude) , 
#           ) 
#         session.add(outlet)
#         session.commit()
#         session.refresh(outlet)
        
#         customer = WalkInCustomer(
#             name = valid.customer_name,
#             email= valid.customer_email,
#             # longitude= valid.longitude,
#             # latitude= valid.latitude,
#             route = valid.route,
#             territoy= valid.territoy,


#         )
#         session.add(customer)
#         session.commit()
#         session.refresh(customer)

#         return customer

#     except HTTPException as http_exc:
#         raise http_exc
#     except Exception:
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail="Something went wrong")



@c.post(endpoint['create'])
def create_point_of_sale(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    valid: TemplateView,
):
    try:
        if not check_permission(session, "Create", role_modules['create'], current_user):
            raise HTTPException(status_code=403, detail="You do not have the required privilege")
            
        def parse_float(val):
            if val == "":
                return None
            if isinstance(val, float):
                return val
            try:
                return float(val)
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="Latitude/Longitude must be a float or null.")

        # Make sure that only one type of detail is provided
        if valid.outlet_name and valid.customer_name:
            raise HTTPException(
                status_code=400,
                detail="Provide either outlet details or customer details, not both."
            )

        # Initialize IDs to None
        outlet_id = None
        walk_in_customer_id = None

        # If outlet details are provided, create the outlet
        if valid.outlet_name:
            # Convert the channel to a ChannelType enum.
            # If the value is an integer, we treat it as an index into the enum.
            if isinstance(valid.channel, int):
                try:
                    channel_enum = list(ChannelType)[valid.channel]
                except IndexError:
                    raise HTTPException(status_code=400, detail="Invalid channel index provided.")
            else:
                try:
                    channel_enum = ChannelType(valid.channel)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid channel value provided.")

            outlet = Outlet(
                outlet_name=valid.outlet_name,
                channel=[channel.value for channel in ChannelType][valid.channel],  # Pass the validated enum member here
                tin=valid.tin,
                phone=valid.phone,
                emaioutlet_emaill=valid.outlet_email,
                latitude=parse_float(valid.latitude),
                longitude=parse_float(valid.longitude)
            )
            session.add(outlet)
            session.commit()
            session.refresh(outlet)
            outlet_id = outlet.id
            # Since outlet is provided, we set walk-in customer id to None explicitly.
            walk_in_customer_id = None
        else:
            # Otherwise, create the walk-in customer (and outlet_id remains None)
            customer = WalkInCustomer(
                customer_name=valid.customer_name,
                customer_email=valid.customer_email,
                route=valid.route,
                territoy=valid.territoy
            )
            session.add(customer)
            session.commit()
            session.refresh(customer)
            walk_in_customer_id = customer.id

        # Determine organization; either from valid or by scope of the user.

        org = fetch_organization_ids(session, current_user)
  # Choose the desired organization
        # Create the PointOfSale record ensuring one (and only one) is set.
        pos = PointOfSale(
            status=POSStatus.INACTIVE,  # Use the enum directly
            registered_on=datetime.utcnow().isoformat(),  # ISO-formatted UTC datetime
            organization=org,  # A single organization ID is expected
            outlet=outlet_id,                # Only one of these will be non-null
            walk_in_customer=walk_in_customer_id
        )
        session.add(pos)
        session.commit()
        session.refresh(pos)

        return pos

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")
@c.put(endpoint['update'])
def update_point_of_sale(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    id: int,
    valid: TemplateViews
):
    try:
        if not check_permission(session, "Update", role_modules['update'], current_user):
            raise HTTPException(status_code=403, detail="You do not have the required privilege")

        entry = session.get(db_model, valid.id)

        if not entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

        # Update fields
        entry.status = valid.status
        entry.registered_on = valid.registered_on
        entry.organization = valid.organization
        entry.outlet_id = valid.outlet_id
        entry.walk_in_customer_id = valid.walk_in_customer_id

        session.add(entry)
        session.commit()
        session.refresh(entry)

        return entry

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")


@c.delete(endpoint['delete'])
def delete_point_of_sale(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    id: int
):
    try:
        if not check_permission(session, "Delete", role_modules['delete'], current_user):
            raise HTTPException(status_code=403, detail="You do not have the required privilege")

        entry = session.get(db_model, id)

        if not entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

        session.delete(entry)
        session.commit()

        return {"detail": f"{endpoint_name} deleted successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")