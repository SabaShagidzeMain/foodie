from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary"""
    if dictionary is None:
        return {}
    return dictionary.get(key, {})

@register.filter
def multiply(value, arg):
    """Multiply a value by an argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value