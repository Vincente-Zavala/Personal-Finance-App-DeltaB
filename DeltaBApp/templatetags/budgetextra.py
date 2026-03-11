from django import template
import calendar

register = template.Library()

@register.filter
def getitem(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def tolist(start, end):
    """Generate list of numbers from start to end (inclusive)."""
    return range(start, end+1)

@register.filter
def yearrange(startyear, count):
    """Generate a list of years starting at start_year for count years."""
    return range(startyear, startyear + count)

@register.filter
def monthname(monthnumber):
    """Convert a month number (1–12) into the full month name."""
    return calendar.month_name[monthnumber]


@register.filter
def month_name(month_number):

        return calendar.month_name[int(month_number)]


@register.filter
def abs_val(value):
    return abs(value)