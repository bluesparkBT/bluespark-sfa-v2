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
}
