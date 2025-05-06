import re


def capitalize_name(name: str) -> str:
    """Validates if the name consists of 2 or 3 parts, with proper capitalization."""
    name_parts = name.split()
    name_parts = [part.lower().capitalize() for part in name_parts]

    formatted_name = " ".join(name_parts)
    return formatted_name


def validate_name(name: str) -> bool:
    if not name.replace(" ", "").isalpha():
        return False

    name_parts = name.split()
    if len(name_parts) < 2 or len(name_parts) > 3:
        return False

    return True


def validate_email(email: str) -> bool:
    """Validates if the email address is in a valid format using regex."""
    email_regex = r"^[a-z0-9._]+@[a-z0-9.-]+\.[a-z]{2,}$"

    if re.match(email_regex, email):
        return True
    return False


def is_valid_phone_number(phone_number: str) -> str:
    """Validates phone number and returns it in the correct format starting with +251."""
    phone_number = phone_number.replace(" ", "")
    phone_regex = r"^\+\d{1,3}\d{10}$"
    zero_regex = r"^0\d{9}$"

    if re.match(phone_regex, phone_number) or re.match(zero_regex, phone_number):
        return True
    return False

