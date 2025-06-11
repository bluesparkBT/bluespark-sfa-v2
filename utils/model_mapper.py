MODEL_HTML_TYPES = {

    "organization": {
        "id": "hidden",
        "name": "text",
        "owner_name": "text",
        "description": "textarea",
        "logo_image": "file",
        "parent_organization": "select",
        "parent_id": "select",
        "organization_type": "select",
        "inheritance_group": "select",
        "address": "select",
        "landmark": "text",
        "hidden": "text",
    },
    "tenant": {
        "id": "hidden",
        "name": "text",
        "owner_name": "text",
        "logo_image": "file",
        "description": "textarea",
        "parent_organization": "select",
        "country": "text",
        "city": "text",
        "sub_city": "text",
        "woreda": "text",
        "landmark": "text",
        "hidden": "text",
    },
    "role":{
        "id":"hidden",
        "name":"text",
        "module":"select",
        "policy":"radio",
        "permissions": "hidden"
    },
    "policy":{
        "role":"hidden",
       
    },
    "scope_group":{
        "id":"hidden",
        "name":"text",
        "hidden": "hierarchical-checkbox"
    },
    
    "user": {
        "id": "hidden",
        "full_name": "text",
        "username": "text",
        "email": "text",
        "phone_number": "text",
        "organization": "select",
        "role": "select",
        "scope": "select",
        "scope_group": "select",
        "gender": "select",
        "salary": "number",
        "position": "text",        
        "date_of_birth": "date",
        "date_of_joining": "date",
        "manager": "select",
        "image": "file",
        "id_type": "select",
        "id_number": "text",
        "address" : "select",
        # "old_password": "text",
        # "password": "text"

    },
    "address": {
        "id": "hidden",
        "country": "text",
        "city": "text",
        "sub_city": "text",
        "woreda": "text",
        "organization": "select"
    },
    "location": {
        "id": "hidden",
        "name": "text",
        "address": "select",
        "latitude": "number",
        "longitude": "number",
    },
    "warehouse":{
        "id":"hidden",
        "warehouse_name":"text",
        "organization":"select",
        "address": "select",
        "landmark": "text",
        "latitude":"text",
        "longitude": "text",
    },
      "warehouse-storeadmin-add":{
        "warehouse_group":"select",
        "store_admins": "select multiple"
    },
     "warehouse-storeadmin-update":{
        "warehouse_group":"hidden",
        "store_admins": "select multiple"
    },
    "warehouse-group":{
        "name": "text",
        "access_policy": "select",
        "warehouses": "select multiple"
    },
    "stock":{
        "id":"hidden",
        "product":"select",
        "quantity": "number",
        "stock_type": "select"
    },
    "warehouse_stop":{
        "id":"hidden",
        "request_type":"select",
        "vehicle":"select",
        "product": "select",
        "warehouse": "select",
        "quantity": "number",
        "stock_type": "select"
    },
    "category": {
        "id": "hidden",
        "name": "text",
        "code": "text",
        "description": "textarea",
        "parent_category": "select",
        "organization": "select"
    },
    "product": {
        "id": "hidden",
        "name": "text",
        "sku": "text",
        "organization": "select",
        "category": "select",        
        "description": "textarea",
        "image": "file",
        "brand": "text",
        "price": "number",
        "unit": "select",

    },
    "inheritance": {
        "id": "hidden",
        "name": "text",
        "organization": "select",
        "category": "select",
        "product": "select",
        "role": "select",
        "classification": "select",
        "point_of_sale": "select"
    },
    "deposit": {
        "id": "hidden",
        "bank": "select",
        "account": "select",
        "branch": "text",
        "amount": "number",
        "remark": "text",
        "date": "date",
        "organization": "select",
        "transaction_number":"text",
        "deposit_slip": "file"
    },
    "bank": {
        "id": "hidden",
        "bank_name": "select",
        "account": "text",
        "account_holder": "text",
        "organization": "select"
    },

    "product": "select"
        # "classification":"select"
    },
    "classification":{
        "id": "hidden",
        "name": "text",
        "organization": "select",
        "point_of_sale": "select",
        "route":"select",
        "territory":"select",
        "description": "textarea",

        "customer_id": "hidden",
        "start_date": "date",
        "end_date": "date",
        "discount": "number"
    },

    "territory": {

            "id": "hidden",
            "country": "text",
            "name": "text",
            "description": "textarea",
            "organization": "select",          
    },
    "customer_discount":{
            "id": "",
            "start_date": "",
            "end_date": "",
            "discount": "",            
    },
    "outlet":{
            "id": "hidden",
            "outlet_name": "text",
            "channel": "select",
            "tin": "text",
            "phone": "text",
            "outlet_email": "text",
            "latitude": "text",
            "longitude": "text",
   } ,
    "walk_in":{
            "id": "hidden",
            "name": "text",
            "email": "text",
            "location":"select",
            "route":"select",
            "territory":"select",
            "organization":"select" ,
    },
    "route": {
            "id": "hidden",
            "name": "text",
            "territory": "select",
            "description": "textarea",
            "organization": "select"      
    },
    "point_of_sale": {

            "id": "hidden",
            "outlet_name": "text",
            "channel": "select",
            "tin": "text",
            "phone": "text",
            "outlet_email": "text",
            "latitude": "hidden",
            "longitude": "hidden",

            "customer_id": "hidden",
            "customer_name": "text",
            "customer_email": "text",
            "route": "select",
            "territoy": "select",
            },
}
  