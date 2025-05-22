from datetime import datetime
from http.client import HTTPException
import re
from typing import Optional

from models.Account import Scope


def capitalize_name(name: str) -> str:
    """Validates if the name consists of 2 or 3 parts, with proper capitalization."""
    name_parts = name.split()
    name_parts = [part.lower().capitalize() for part in name_parts]

    formatted_name = " ".join(name_parts)
    return formatted_name


def validate_name(name: str) -> bool:
    name_match = re.match(r"^([0-9A-Za-z \u1200-\u137f\-&_]*)$", name)
    
    if name_match:
        return True
    else:
        return False 
    
def validate_image(image_b64str: str) -> bool:
    """Validates if the image string is in a valid base64 format."""
    if re.match(r"^data:image/(jpeg|png|jpg);base64,[A-Za-z0-9+/=]+$", image_b64str):
        return True
    else:
        return False
    

def validate_email(email: str) -> bool:
    """Validates if the email address is in a valid format (RFC 5322 simplified)."""
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(email_regex, email) is not None


def validate_phone_number(phone_number) -> bool:
    """Validates Ethiopian phone numbers starting with +2517/9 or 07/09."""
    if not phone_number:
        return False

    phone_number = str(phone_number).replace(" ", "")
    # Matches +251 followed by 7xx or 9xx and 7 more digits
    phone_regex = r"^\+251[79]\d{8}$"
    # Matches local format like 07xxxxxxxx or 09xxxxxxxx
    local_regex = r"^0[79]\d{8}$"

    return bool(re.match(phone_regex, phone_number) or re.match(local_regex, phone_number))

def parse_datetime_field(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid date format. Use ISO format like 'YYYY-MM-DD'."
            )
        
def format_date_for_input(dt: Optional[datetime]) -> str:
    return dt.strftime('%Y-%m-%d') if dt else ""

def parse_enum(enum_class, value: Optional[str], field_name: str):
    if not value:
        if enum_class == Scope:
            return Scope.personal_scope
        return None
    try:
        return enum_class(value)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid value for {field_name}: '{value}'"
        )

