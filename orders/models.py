from django.db import models


class Order(models.Model):
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
    product_title = models.CharField("Название товара", max_length=255)
    price = models.PositiveIntegerField("Цена, ₽", default=0)
    size = models.CharField("Размер", max_length=30, blank=True)
    name = models.CharField("Имя", max_length=120)
    contact = models.CharField("Telegram / телефон", max_length=120)
    comment = models.TextField("Комментарий", blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"

    def __str__(self):
        return f"#{self.pk} {self.product_title} — {self.name}"
