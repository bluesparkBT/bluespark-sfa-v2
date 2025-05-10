MODEL_HTML_TYPES = {

    "Organization": {
        "id": "hidden",
        "organization_name": "text",
        "owner_name": "text",
        "description": "textarea",
        "logo_image": "file",
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
    }
}
