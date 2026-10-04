from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.models import Orderable


class Order(ClusterableModel):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        CONTACTED = "contacted", "Связались"
        PAID = "paid", "Оплачена"
        SHIPPED = "shipped", "Отправлена"
        CANCELLED = "cancelled", "Отменена"

    created_at = models.DateTimeField("Создана", auto_now_add=True)
    status = models.CharField("Статус", max_length=12, choices=Status.choices, default=Status.NEW)
    product = models.ForeignKey(
        "catalog.ProductPage", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="orders", verbose_name="Товар",
    )
    # Snapshot, so the order stays readable if the product changes or is deleted.
    # For cart orders this is a one-line summary of all items.
    product_title = models.CharField("Товары", max_length=255)
    price = models.PositiveIntegerField("Сумма, ₽", default=0)
    size = models.CharField("Размер", max_length=30, blank=True)
    name = models.CharField("Имя", max_length=120)
    contact = models.CharField("Telegram / телефон", max_length=120)
    comment = models.TextField("Комментарий", blank=True)

    panels = [
        FieldPanel("status"),
        MultiFieldPanel([FieldPanel("name"), FieldPanel("contact"), FieldPanel("comment")], heading="Покупатель"),
        InlinePanel("items", label="Позиция"),
        FieldPanel("price"),
    ]

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"

    def __str__(self):
        return f"#{self.pk} {self.product_title} — {self.name}"


class OrderItem(Orderable):
    order = ParentalKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.ProductPage", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+", verbose_name="Товар",
    )
    title = models.CharField("Название", max_length=255)
    size = models.CharField("Размер", max_length=30, blank=True)
    quantity = models.PositiveIntegerField("Кол-во", default=1)
    price = models.PositiveIntegerField("Цена за шт., ₽", default=0)

    panels = [FieldPanel("title"), FieldPanel("size"), FieldPanel("quantity"), FieldPanel("price")]

    class Meta(Orderable.Meta):
        verbose_name = "Позиция"
        verbose_name_plural = "Позиции"

    def __str__(self):
        size = f" ({self.size})" if self.size else ""
        return f"{self.title}{size} × {self.quantity}"

    @property
    def line_total(self):
        return self.price * self.quantity
