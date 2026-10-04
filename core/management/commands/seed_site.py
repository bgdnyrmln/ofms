from django.core.management.base import BaseCommand
from wagtail.models import Page, Site

from catalog.models import CatalogIndexPage, Category, ProductPage
from core.models import ContentPage, SiteSettings
from home.models import HomePage


class Command(BaseCommand):
    help = "Create the page tree (Home, Catalog, About, Contacts). Use --demo for sample products."

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Add sample products (no photos)")

    def handle(self, *args, **opts):
        if HomePage.objects.exists():
            self.stdout.write("Home page already exists, skipping tree creation.")
            home = HomePage.objects.first()
        else:
            root = Page.get_first_root_node()
            home = HomePage(title="Главная", slug="home-new", hero_title="Новая коллекция")
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
        if not ContentPage.objects.filter(slug="contacts").exists():
            home.add_child(instance=ContentPage(title="Контакты", slug="contacts", show_in_menus=True))

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
