MODEL_HTML_TYPES = {

    "Organization": {
        "id": "hidden",
        "organization_name": "text",
        "owner_name": "text",
        "description": "textarea",
        "logo_image": "file",
        "parent_organization": "select",
        "organization_type": "select",
    },
    "Role":{
        "id":"hidden",
        "name":"text",
    },
    "Policy":{
        "role_id":"hidden",
        "module":"select",
        "policy":"radio"
    },
    "scope_group":{
        "id":"hidden",
        "name":"text",
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
    "scope_organization":{
        "scope_id":"hidden",
        "organizations":"checkbox",
    },
}
