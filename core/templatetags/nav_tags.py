import os

from django import template
from wagtail.models import Site

register = template.Library()


@register.simple_tag(takes_context=True)
def main_menu(context):
    request = context.get("request")
    site = Site.find_for_request(request) if request else None
    if not site:
        return []
    return site.root_page.get_children().live().in_menu().specific()


@register.filter
def rub(value):
    try:
        return f"{int(value):,}".replace(",", "\u202f") + "\u00a0₽"
    except (TypeError, ValueError):
        return ""


@register.simple_tag
def asset(path):
    """Static URL with the file's mtime appended, so browsers drop a stale
    copy as soon as the file changes (plain /static/ URLs get cached)."""
    from django.contrib.staticfiles import finders
    from django.templatetags.static import static

    url = static(path)
    found = finders.find(path)
    if found:
        url += "?v=%d" % os.path.getmtime(found)
    return url
