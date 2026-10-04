from django.db import models, transaction
from django.shortcuts import redirect
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.snippets.models import register_snippet

from orders.forms import OrderForm
from orders.notifications import notify_new_order


@register_snippet
class Category(models.Model):
    name = models.CharField("Название", max_length=80)
    slug = models.SlugField("Слаг", unique=True)

    panels = [FieldPanel("name"), FieldPanel("slug")]

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name


class CatalogIndexPage(Page):
    intro = models.CharField("Подпись", max_length=200, blank=True)
    content_panels = Page.content_panels + [FieldPanel("intro")]
    parent_page_types = ["home.HomePage"]
    subpage_types = ["catalog.ProductPage"]
    max_count = 1

    class Meta:
        verbose_name = "Каталог"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        products = ProductPage.objects.child_of(self).live().order_by("-first_published_at")
        slug = request.GET.get("category")
        if slug:
            products = products.filter(category__slug=slug)
        context["products"] = products
        context["categories"] = Category.objects.filter(productpage__in=ProductPage.objects.child_of(self).live()).distinct()
        context["active_category"] = slug
        return context


class ProductPage(Page):
    price = models.PositiveIntegerField("Цена, ₽")
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Категория")
    short_description = models.CharField("Короткое описание", max_length=200, blank=True)
    description = RichTextField("Описание", blank=True, features=["bold", "italic", "ul", "link"])
    details = RichTextField("Материалы и уход", blank=True, features=["bold", "ul", "link"])
    sizes = models.CharField("Размеры через запятую", max_length=120, blank=True, help_text="Например: XS, S, M, L. Пусто — без выбора размера.")
    is_available = models.BooleanField("В наличии / можно заказать", default=True)
    featured = models.BooleanField("Показывать на главной", default=False)

    content_panels = Page.content_panels + [
        FieldPanel("price"),
        FieldPanel("category"),
        FieldPanel("short_description"),
        FieldPanel("description"),
        FieldPanel("details"),
        FieldPanel("sizes"),
        FieldPanel("is_available"),
        FieldPanel("featured"),
        InlinePanel("images", label="Фото", min_num=0),
    ]
    parent_page_types = ["catalog.CatalogIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    @property
    def size_list(self):
        return [s.strip() for s in self.sizes.split(",") if s.strip()]

    @property
    def main_image(self):
        first = self.images.first()
        return first.image if first else None

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["form"] = getattr(request, "_order_form", None) or OrderForm(sizes=self.size_list)
        context["ordered"] = request.GET.get("ordered") == "1"
        return context

    def serve(self, request, *args, **kwargs):
        if request.method == "POST" and self.is_available:
            form = OrderForm(request.POST, sizes=self.size_list)
            if form.is_valid():
                order = form.save(commit=False)
                order.product, order.product_title, order.price = self, self.title, self.price
                order.save()
                transaction.on_commit(lambda: notify_new_order(order))
                return redirect(self.url + "?ordered=1#order")
            request._order_form = form
        return super().serve(request, *args, **kwargs)


class ProductImage(Orderable):
    page = ParentalKey(ProductPage, on_delete=models.CASCADE, related_name="images")
    image = models.ForeignKey("wagtailimages.Image", on_delete=models.CASCADE, related_name="+")
    caption = models.CharField(max_length=120, blank=True)
    panels = [FieldPanel("image"), FieldPanel("caption")]
