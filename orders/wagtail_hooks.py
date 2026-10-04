from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import Order


class OrderViewSet(SnippetViewSet):
    model = Order
    icon = "form"
    menu_label = "Заявки"
    menu_order = 200
    add_to_admin_menu = True
    list_display = ["created_at", "product_title", "size", "name", "contact", "status"]
    list_filter = ["status"]
    search_fields = ["name", "contact", "product_title"]


register_snippet(OrderViewSet)
