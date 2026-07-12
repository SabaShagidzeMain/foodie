from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary"""
    if dictionary is None:
        return {}
    return dictionary.get(key, {})