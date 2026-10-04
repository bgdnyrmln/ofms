from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page


class HomePage(Page):
    hero_title = models.CharField("Заголовок", max_length=120, blank=True)
    hero_subtitle = models.CharField("Подзаголовок", max_length=200, blank=True)
    hero_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+", verbose_name="Главное фото (кампания)",
    )

    content_panels = Page.content_panels + [
        FieldPanel("hero_title"),
        FieldPanel("hero_subtitle"),
        FieldPanel("hero_image"),
    ]
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = ["catalog.CatalogIndexPage", "core.ContentPage"]
    max_count = 1

    class Meta:
        verbose_name = "Главная страница"

    def get_context(self, request, *args, **kwargs):
        from catalog.models import ProductPage, CatalogIndexPage

        context = super().get_context(request, *args, **kwargs)
        context["featured"] = ProductPage.objects.live().filter(featured=True).order_by("-first_published_at")[:8]
        context["catalog"] = CatalogIndexPage.objects.live().first()
        return context
