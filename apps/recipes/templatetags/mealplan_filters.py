from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary or check if recipe is favorited"""
    if dictionary is None:
        return False
    if hasattr(dictionary, 'favorited_by'):
        # If it's a recipe, check if user has favorited it
        return dictionary.favorited_by.filter(user=key).exists()
    return dictionary.get(key, {})

@register.filter
def multiply(value, arg):
    """Multiply a value by an argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value