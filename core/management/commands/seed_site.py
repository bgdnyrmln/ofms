from django.core.management.base import BaseCommand
from wagtail.models import Page, Site

from catalog.models import CatalogIndexPage, Category, ProductPage
from core.models import ContentPage, SiteSettings
from home.models import HomePage

# Draft store rules. Edit them in the admin: Pages → Правила.
RULES = [
    ("heading", "Общие положения"),
    ("text", "<p>Оформляя заявку на сайте, вы соглашаетесь с этими правилами. Заявка не является оплатой: заказ считается подтверждённым после того, как менеджер свяжется с вами и вы согласуете детали.</p>"),
    ("heading", "Оформление заказа"),
    ("text", "<ul><li>Добавьте вещи в корзину, укажите размер и оставьте контакт — Telegram или телефон.</li><li>Мы напишем в течение 24 часов, подтвердим наличие, размер, стоимость доставки и способ оплаты.</li><li>Если не удаётся связаться с вами в течение 3 дней, заявка отменяется.</li></ul>"),
    ("heading", "Оплата"),
    ("text", "<p>Способ оплаты согласовывается с менеджером. Вещь резервируется за вами после оплаты. Изделия под заказ запускаются в работу после предоплаты.</p>"),
    ("heading", "Сроки и доставка"),
    ("text", "<ul><li>Вещи в наличии отправляем в течение 3–5 рабочих дней после оплаты.</li><li>Срок изготовления изделий под заказ сообщаем индивидуально.</li><li>Доставка по России транспортной компанией, стоимость доставки оплачивает покупатель. После отправки присылаем трек-номер.</li></ul>"),
    ("heading", "Возврат и обмен"),
    ("text", "<ul><li>Вещь надлежащего качества можно вернуть в течение 7 дней после получения, если сохранены товарный вид, бирки и упаковка. Стоимость обратной доставки оплачивает покупатель.</li><li>Изделия, изготовленные под заказ по индивидуальным параметрам, возврату и обмену не подлежат, если у них нет дефектов.</li><li>Если вы обнаружили брак, напишите нам в течение 7 дней после получения и приложите фото — мы заменим вещь или вернём деньги.</li></ul>"),
    ("heading", "Особенности изделий"),
    ("text", "<p>Вещи делаются вручную, поэтому каждая немного отличается: оттенок, потёртости и расположение деталей могут не совпадать с фото. Это не считается браком.</p>"),
    ("heading", "Персональные данные"),
    ("text", "<p>Имя и контакт, которые вы оставляете в заявке, используются только для связи по заказу и не передаются третьим лицам, кроме службы доставки.</p>"),
]


class Command(BaseCommand):
    help = "Create the page tree (Home, Catalog, About, Rules). Use --demo for sample products."

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Add sample products (no photos)")

    def handle(self, *args, **opts):
        if HomePage.objects.exists():
            self.stdout.write("Home page already exists, skipping tree creation.")
            home = HomePage.objects.first()
        else:
            root = Page.get_first_root_node()
            home = HomePage(title="Главная", slug="home-new", hero_title="Новая коллекция",
                            marquee="Доставка по РФ, Ручная работа, Ограниченный тираж, Изделия под заказ")
            root.add_child(instance=home)
            site = Site.objects.get(is_default_site=True)
            old = site.root_page
            site.root_page = home
            site.save()
            if old.specific_class is Page:
                old.delete()
            home.slug = "home"
            home.save()
            self.stdout.write("Created home page.")

        if not CatalogIndexPage.objects.exists():
            home.add_child(instance=CatalogIndexPage(title="Каталог", slug="catalog", show_in_menus=True))
        if not ContentPage.objects.filter(slug="about").exists():
            home.add_child(instance=ContentPage(title="О бренде", slug="about", show_in_menus=True))
        if not ContentPage.objects.filter(slug="rules").exists():
            home.add_child(instance=ContentPage(title="Правила", slug="rules", show_in_menus=True, body=RULES, accordion=True))

        site = Site.objects.get(is_default_site=True)
        SiteSettings.for_site(site)

        if opts["demo"] and not ProductPage.objects.exists():
            catalog = CatalogIndexPage.objects.first()
            cats = {s: Category.objects.get_or_create(name=n, slug=s)[0]
                    for n, s in [("Верхняя одежда", "outerwear"), ("Трикотаж", "knit"), ("Аксессуары", "accessories")]}
            demo = [
                ("Пальто Нева", "palto-neva", 38000, "outerwear", "XS, S, M, L", True),
                ("Свитер Лето", "sviter-leto", 14500, "knit", "S, M, L", True),
                ("Шарф Пепел", "sharf-pepel", 6200, "accessories", "", False),
                ("Бомбер Двор", "bomber-dvor", 21000, "outerwear", "S, M, L, XL", True),
            ]
            for title, slug, price, cat, sizes, featured in demo:
                catalog.add_child(instance=ProductPage(
                    title=title, slug=slug, price=price, category=cats[cat], sizes=sizes, featured=featured, is_available=(slug != "sharf-pepel"),
                    short_description="Демо-товар. Замените описание и добавьте фото в админке.",
                ))
            self.stdout.write("Created demo products.")
        self.stdout.write(self.style.SUCCESS("Done."))
