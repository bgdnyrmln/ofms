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


@register.filter
def ru_plural(value, forms):
    """{{ n|ru_plural:"товар,товара,товаров" }} -> "5 товаров"."""
    one, few, many = forms.split(",")
    n = abs(int(value))
    if n % 10 == 1 and n % 100 != 11:
        word = one
    elif 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        word = few
    else:
        word = many
    return f"{value} {word}"


@register.simple_tag(takes_context=True)
def page_by_slug(context, slug):
    """A live page directly under the site root, e.g. the rules page."""
    request = context.get("request")
    site = Site.find_for_request(request) if request else None
    if not site:
        return None
    return site.root_page.get_children().live().filter(slug=slug).first()


@register.simple_tag
def shop_categories():
    from catalog.models import Category, ProductPage

    return Category.objects.filter(productpage__in=ProductPage.objects.live()).distinct()


@register.simple_tag
def catalog_page():
    from catalog.models import CatalogIndexPage

    return CatalogIndexPage.objects.live().first()
