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
        "latitude": "text",
        "longitude": "text",
        "hidden": "text"
    },
    "role":{
        "id":"hidden",
        "name":"text",
        "module":"select",
        "policy":"radio"
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
        "password": "text"

    },
    "address": {
        "id": "hidden",
        "country": "text",
        "city": "text",
        "sub_city": "text",
        "woreda": "text",
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
        "location":"text"
    },
     "warehouse_storeadmin":{
        "warehouse_id":"hidden",
        "store_admin": "checkbox"
    },
    "stock":{
        "id":"hidden",
        "warehouse":"select",
        "product":"select",
        "category":"select",
        "sub_category": "select",
        "quantity": "number",
        "stock_type": "select"
    },
    "warehouse_stop":{
        "id":"hidden",
        "request_type":"select",
        "vehicle":"select",
        "stock": "select",
        "quantity": "number",
        "stock_type": "select"
    },
    "category": {
        "id": "hidden",
        "name": "text",
        "code": "text",
        "description": "textarea",
        "image": "file",
        "parent_category": "select",
        "organization": "select"
    },
    "product": {
        "id": "hidden",
        "sku": "text",
        "name": "text",
        "description": "textarea",
        "image": "file",
        "brand": "text",
        "price": "number",
        "unit": "select",
        "category": "select",
        "organization": "select"
    },
    "inheritance": {
        "id": "hidden",
        "name": "text",
        "category": "select",
        "product": "select"
    }

}
