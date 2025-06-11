import traceback
from datetime import datetime
from fastapi import Depends, HTTPException, Body, APIRouter
from typing import Annotated, Optional
from fastapi.routing import APIRouter
from sqlmodel import and_, select, Session
from db import get_session
from models.PointOfSale import PointOfSale, Outlet, WalkInCustomer,ChannelType, POSStatus
from models.Utils import ErrorLog
from models.Address import Geolocation
from models.Account import Organization
from utils.util_functions import parse_float
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
    "get_by_id": f"/get-{endpoint_name}/",
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


@c.get(endpoint['get_by_id'] + "/{id}")
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
            raise HTTPException(status_code=404, detail= f"{endpoint_name} not found")
              
        outlet = session.exec(
            select(Outlet).where(Outlet.id == entry.outlet_id)
        ).first()
        walkIncustomer = session.exec(
            select(WalkInCustomer).where(WalkInCustomer.id == entry.walk_in_customer_id)
        ).first()
        location = session.exec(select (Geolocation).where(Geolocation.id == outlet.location_id)).first()   

        if not entry:
            raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

        pointofsale = {
            "id": entry.id,
            "outlet_name": outlet.name,
            "channel": outlet.channel,
            "tin": outlet.tin,
            "phone": outlet.phone,
            "outlet_email": outlet.email,
            "latitude": location.latitude,
            "longitude": location.longitude,

            "customer_id": walkIncustomer.id ,
            "customer_name": walkIncustomer.name,
            "customer_email": walkIncustomer.email,
            "route": walkIncustomer.route_id,
            "territoy": walkIncustomer.territoy_id,
        }

        return pointofsale

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")



@c.get(endpoint['get_form'])
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



@c.post(endpoint['create'] )
def create_point_of_sale(
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    valid: TemplateView,
):
    try:
        if not check_permission(session, "Create", role_modules['create'], current_user):
            raise HTTPException(status_code=403, detail="You do not have the required privilege")
            
        # def parse_float(val):
        #     if val == "":
        #         return None
        #     if isinstance(val, float):
        #         return val
        #     try:
        #         return float(val)
        #     except (TypeError, ValueError):
        #         raise HTTPException(status_code=400, detail="Latitude/Longitude must be a float or null.")

        # Make sure that only one type of detail is provided
        if valid.outlet_name and valid.customer_name:
            raise HTTPException(
                status_code=400,
                detail="Provide either outlet details or customer details, not both."
            )

        # Initialize IDs to None
        outlet_id = None
        walk_in_customer_id = None
        print ("thisssssssss is outlet name", valid.outlet_name)
        # If outlet details are provided, create the outlet
        if valid.outlet_name and valid.outlet_name.strip() != "":
            print("this is the outlet name and it is not none",valid.outlet_name)
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

            # Create the outlet with validated data
            address = Geolocation(
                name= valid.outlet_name,
                latitude=parse_float(valid.latitude),
                longitude=parse_float(valid.longitude),


            )
            print(address)
            session.add(address)
            session.commit()
            session.refresh(address)

            outlet = Outlet(
                name=valid.outlet_name,
                channel=[channel.value for channel in ChannelType][valid.channel],  # Pass the validated enum member here
                tin=valid.tin,
                phone=valid.phone,
                outlet_email=valid.outlet_email,
                location_id=address.id
            )
            session.add(outlet)
            session.commit()
            session.refresh(outlet)
            
            org_id = fetch_organization_ids(session, current_user) 
            print ("fetch orgggggg",org_id) # Returns list of IDs
    
            # Get the first organization object (assuming there's at least one)
            organization = session.exec(select(Organization).where(Organization.id == org_id[0])).first()
            print("this is the organization", organization)  # returns tuple if available, or None
            last_id = session.exec(
                    select(Outlet.id).order_by(Outlet.id.desc())
                ).first()
            print("this is the last outlate idd", last_id)  # returns tuple if available, or None
            organization_id = org_id[0] 
            # Pass the ORM object instead of just the integer ID
            pos = PointOfSale(
                organization=organization_id,  # ✅ Now passing ORM object
                status=POSStatus.INACTIVE,
                registered_on=datetime.utcnow().isoformat(),
                outlet_id=last_id,
                # walk_in_customer=walk_last_id
            )
            session.add(pos)
            session.commit()
            session.refresh(pos)
            return pos
            # Since outlet is provided, we set walk-in customer id to None explicitly.
            
        else:
            # Otherwise, create the walk-in customer (and outlet_id remains None)
            customer = WalkInCustomer(
                name=valid.customer_name,
                email=valid.customer_email,
                route_id=valid.route,
                territoy_id=valid.territoy
            )
            session.add(customer)
            session.commit()
            session.refresh(customer)
            org_id = fetch_organization_ids(session, current_user) 
            print ("fetch orgggggg",org_id)         
            organization = session.exec(select(Organization).where(Organization.id == org_id[0])).first()
            print("this is the organization", organization)  # returns tuple if available, or None
            last_id = session.exec(
                    select(WalkInCustomer.id).order_by(WalkInCustomer.id.desc())
                ).first()
            print("this is the last wak in customer id", last_id)  # returns tuple if available, or None
            organization_id = org_id[0] 
            # Pass the ORM object instead of just the integer ID
            pos = PointOfSale(
                organization=organization_id,  # ✅ Now passing ORM object
                status=POSStatus.INACTIVE,
                registered_on=datetime.utcnow().isoformat(),
                #outlet_id=last_id,
                walk_in_customer_id= last_id
            )
            session.add(pos)
            session.commit()
            session.refresh(pos)
            return pos
        # Determine organization; either from valid or by scope of the user.


    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong")


# @c.put(endpoint['update'])
# def update_point_of_sale(
#     session: SessionDep,
#     tenant: str,
#     current_user: UserDep,
#     id: int,
#     valid: TemplateViews
# ):
#     try:
#         if not check_permission(session, "Update", role_modules['update'], current_user):
#             raise HTTPException(status_code=403, detail="You do not have the required privilege")

#         entry = session.get(db_model, valid.id)

#         if not entry:
#             raise HTTPException(status_code=404, detail=f"{endpoint_name} not found")

#         # Update fields
#         entry.status = valid.status
#         entry.registered_on = valid.registered_on
#         entry.organization = valid.organization
#         entry.outlet_id = valid.outlet_id
#         entry.walk_in_customer_id = valid.walk_in_customer_id

#         session.add(entry)
#         session.commit()
#         session.refresh(entry)

#         return entry

#     except HTTPException as http_exc:
#         raise http_exc
#     except Exception:
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail="Something went wrong")
@c.put(endpoint['update'] + "/{id}")
def update_point_of_sale(
    # pos_id: int,
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
    valid: TemplateViews,
):
    try:
        if not check_permission(session, "Update", role_modules['create'], current_user):
            raise HTTPException(status_code=403, detail="You do not have the required privilege")

        pos = session.get(PointOfSale, valid.id)
        if not pos:
            raise HTTPException(status_code=404, detail="PointOfSale not found")

        def parse_float(val):
            if val == "":
                return None
            if isinstance(val, float):
                return val
            try:
                return float(val)
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="Latitude/Longitude must be a float or null.")

        if valid.outlet_name and valid.customer_name:
            raise HTTPException(
                status_code=400,
                detail="Provide either outlet details or customer details, not both."
            )

        # Handle Outlet Update
        if valid.outlet_name is not None:
            if pos.outlet_id:
                outlet = session.get(Outlet, pos.outlet_id)
                if not outlet:
                    raise HTTPException(status_code=404, detail="Outlet not found")

                # Update address if necessary
                address = session.get(Geolocation, outlet.location_id)
                if address:
                    address.name = valid.outlet_name
                    address.latitude = parse_float(valid.latitude)
                    address.longitude = parse_float(valid.longitude)
                    session.add(address)

                outlet.name = valid.outlet_name
                outlet.channel = [channel.value for channel in ChannelType][valid.channel]
                outlet.tin = valid.tin
                outlet.phone = valid.phone
                outlet.email = valid.outlet_email
                session.add(outlet)

            else:
                raise HTTPException(status_code=400, detail="No existing outlet associated with this POS.")

        # Handle Walk-In Customer Update
        elif valid.customer_name is not None:
            if pos.walk_in_customer_id:
                customer = session.get(WalkInCustomer, pos.walk_in_customer_id)
                if not customer:
                    raise HTTPException(status_code=404, detail="WalkInCustomer not found")

                customer.name = valid.customer_name
                customer.email = valid.customer_email
                customer.route_id = valid.route
                customer.territoy_id = valid.territoy
                session.add(customer)

            else:
                raise HTTPException(status_code=400, detail="No existing walk-in customer associated with this POS.")

        session.commit()
        return {"message": "PointOfSale updated successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong during update")

@c.delete(endpoint['delete'] + "/{id}")
def delete_point_of_sale(
    id: int,
    session: SessionDep,
    tenant: str,
    current_user: UserDep,
):
    try:
        if not check_permission(session, "Delete", role_modules['create'], current_user):
            raise HTTPException(status_code=403, detail="You do not have the required privilege")

        pos = session.get(PointOfSale, id)
        if not pos:
            raise HTTPException(status_code=404, detail="PointOfSale not found")

        # Store IDs before deleting PointOfSale
        outlet_id = pos.outlet_id
        customer_id = pos.walk_in_customer_id

        # First delete the PointOfSale
        session.delete(pos)
        session.commit()

        # Then delete the associated outlet and its location
        if outlet_id:
            outlet = session.get(Outlet, outlet_id)
            if outlet:
                if outlet.location_id:
                    geolocation = session.get(Geolocation, outlet.location_id)
                    if geolocation:
                        session.delete(geolocation)
                session.delete(outlet)

        # Delete associated walk-in customer if exists
        if customer_id:
            customer = session.get(WalkInCustomer, customer_id)
            if customer:
                session.delete(customer)

        session.commit()

        return {"message": f"PointOfSale with ID {id} and related entities deleted successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong during deletion")

# @c.delete(endpoint['delete'] + "/{id}")
# def delete_point_of_sale(
#     id: int,
#     session: SessionDep,
#     tenant: str,
#     current_user: UserDep,
# ):
#     try:
#         if not check_permission(session, "Delete", role_modules['create'], current_user):
#             raise HTTPException(status_code=403, detail="You do not have the required privilege")

#         pos = session.get(PointOfSale, id)
#         print ("thisssssssssssssssssssssssssssssssssssssssssssssss is the pos",pos)
#         if not pos:
#             raise HTTPException(status_code=404, detail="PointOfSale not found")

#         # Delete associated outlet (and its geolocation) if exists
#         if pos.outlet_id:
#             outlet = session.get(Outlet, pos.outlet_id)
#             if outlet:
#                 if outlet.location_id:
#                     geolocation = session.get(Geolocation, outlet.location_id)
#                     if geolocation:
#                         session.delete(geolocation)
#                 session.delete(outlet)

#         # Delete associated walk-in customer if exists
#         if pos.walk_in_customer_id:
#             customer = session.get(WalkInCustomer, pos.walk_in_customer_id)
#             if customer:
#                 session.delete(customer)

#         # Delete the PointOfSale itself
#         session.delete(pos)
#         session.commit()

#         return {"message": f"PointOfSale with ID {id} and related entities deleted successfully"}

#     except HTTPException as http_exc:
#         raise http_exc
#     except Exception:
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail="Something went wrong during deletion")
