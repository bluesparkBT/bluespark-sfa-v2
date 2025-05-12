from utils.model_mapper import MODEL_HTML_TYPES


def get_html_types(model_class: type | str) -> str:
    """
    Get the HTML type configuration for a given model class or its name.

    Args:
        model_class (type | str): The class or the name of the model.

    Returns:
        str: The HTML type configuration for the model.
    """
    key = model_class if isinstance(model_class, str) else model_class.__name__
    return MODEL_HTML_TYPES[key]
