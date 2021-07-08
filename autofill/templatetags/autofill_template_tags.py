from django import template

register = template.Library()

@register.filter(name='split')
def split(value, key):
    return value.split(key)[0]

@register.filter
def format_date(date):
    return date.strftime('%Y-%m-%d %H:%M:%S')