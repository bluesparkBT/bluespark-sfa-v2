MODEL_HTML_TYPES = {

    "organization": {
        "id": "hidden",
        "organization_name": "text",
        "tenant_name":"text",
        "owner_name": "text",
        "description": "textarea",
        "logo_image": "file",
        "parent_organization": "select",
        "organization_type": "select",
    },
    "role":{
        "id":"hidden",
        "name":"text",
    },
    "policy":{
        "role_id":"hidden",
        "module":"select",
        "policy":"radio"
    },
    "scope_group":{
        "id":"hidden",
        "name":"text",
    },
    "scope_organization":{
        "scope_id":"hidden",
        "parent_organization": "checkbox",
        "organizations": "hierarchical-checkbox"

    },
    "user": {
        "id": "hidden",
        "full_name": "text",
        "username": "text",
        "phone_number": "text",
        "email": "text",
        "organization": "select",
        "role": "select",
        "scope": "select",
        "scope_group": "select",
        "date_of_birth": "date",
        "date_of_joining": "date",
        "salary": "number",
        "position": "text",
        "image": "file",
        "id_type": "select",
        "id_number": "text",
        "gender": "select",
        "password": "text"
    },
    "address": {
        "id": "hidden",
        "country": "text",
        "city": "text",
        "sub_city": "text",
        "woreda": "text",
        "landmark": "text",
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
        "UNSPC Code": "text",
        "description": "textarea",
        "image": "file",
        "parent_category": "select",
        "organization_id": "select"
    },
    "product": {
        "id": "hidden",
        "sku": "text",
        "name": "text",
        "description": "textarea",
        "image": "file",
        "brand": "text",
        "batch_number": "text",
        "code": "text",
        "price": "number",
        "unit": "text",
        "category": "select",
        "organization_id": "hidden"
    },
    "inheritance": {
        "id": "hidden",
        "name": "text"
    }

}
