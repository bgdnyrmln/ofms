from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.blocks import RichTextBlock, CharBlock
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Page
from django.db import models


@register_setting(icon="cog")
class SiteSettings(BaseSiteSetting):
    brand_name = models.CharField("Название бренда", max_length=60, default="Бренд")
    tagline = models.CharField("Короткое описание", max_length=160, blank=True)
    email = models.EmailField("Email", blank=True)
    telegram = models.CharField("Telegram (без @)", max_length=60, blank=True)
    instagram = models.CharField("Instagram (без @)", max_length=60, blank=True)
    footer_note = models.CharField("Текст в подвале", max_length=200, blank=True)

    panels = [
        FieldPanel("brand_name"),
        FieldPanel("tagline"),
        MultiFieldPanel(
            [FieldPanel("email"), FieldPanel("telegram"), FieldPanel("instagram")],
            heading="Контакты",
        ),
        FieldPanel("footer_note"),
    ]


class ContentPage(Page):
    """Generic page: About, Contacts, Delivery, etc."""

    body = StreamField(
        [
            ("heading", CharBlock(form_classname="title", label="Заголовок")),
            ("text", RichTextBlock(label="Текст")),
            ("image", ImageChooserBlock(label="Фото")),
        ],
        blank=True,
    )

    accordion = models.BooleanField(
        "Разделы гармошкой", default=False,
        help_text="Каждый заголовок становится раскрывающимся разделом (например, для правил).",
    )

    content_panels = Page.content_panels + [FieldPanel("body"), FieldPanel("accordion")]
    parent_page_types = ["home.HomePage"]
    subpage_types = []
    verbose_name = "Текстовая страница"

    class Meta:
        verbose_name = "Текстовая страница"

    def sections(self):
        """Body split at each heading: [(heading or None, [blocks])]."""
        result = []
        for block in self.body:
            if block.block_type == "heading" or not result:
                result.append((block.value if block.block_type == "heading" else None, []))
                if block.block_type == "heading":
                    continue
            result[-1][1].append(block)
        return result
