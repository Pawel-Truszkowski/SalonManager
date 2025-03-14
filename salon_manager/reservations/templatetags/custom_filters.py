from django import template

register = template.Library()


@register.filter
def mul(value, arg):
    return int(value) * int(arg)


@register.filter
def div(value, arg):
    try:
        return int(value) // int(arg)
    except (ValueError, ZeroDivisionError):
        return None
