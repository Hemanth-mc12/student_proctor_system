from django import template

register = template.Library()

@register.filter
def has_attr(obj, attr_name):
    """Check if an object has a specific attribute."""
    return hasattr(obj, attr_name)

@register.filter
def has_group(user, group_name):
    """Check if the user belongs to a specific group."""
    return user.groups.filter(name=group_name).exists()

# ✅ REQUIRED FILTER – FIXES THE ERROR
@register.filter
def get_item(dictionary, key):
    """Safely get a value from a dictionary using a key."""
    try:
        return dictionary.get(key)
    except:
        return None
@register.filter
def has_attr(obj, attr):
    return hasattr(obj, attr)

@register.filter
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()
