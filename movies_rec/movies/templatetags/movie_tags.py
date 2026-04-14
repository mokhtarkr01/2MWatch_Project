from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dict by key (supports int keys)."""
    if dictionary is None:
        return None
    return dictionary.get(key, 0)
