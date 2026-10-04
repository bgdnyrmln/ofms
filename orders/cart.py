"""Session cart. Only product ids, sizes and quantities live in the session;
titles and prices are always read fresh from the catalog."""
from dataclasses import dataclass

SESSION_KEY = "cart"
MAX_QTY = 10


@dataclass
class Line:
    key: str
    product: object
    size: str
    quantity: int

    @property
    def total(self):
        return self.product.price * self.quantity


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.data = self.session.get(SESSION_KEY) or {}

    @staticmethod
    def make_key(product_id, size):
        return f"{product_id}:{size}"

    def _save(self):
        self.session[SESSION_KEY] = self.data
        self.session.modified = True

    def add(self, product, size="", quantity=1):
        key = self.make_key(product.pk, size)
        line = self.data.get(key) or {"id": product.pk, "size": size, "qty": 0}
        line["qty"] = min(line["qty"] + quantity, MAX_QTY)
        self.data[key] = line
        self._save()

    def set_quantity(self, key, quantity):
        if key not in self.data:
            return
        if quantity <= 0:
            del self.data[key]
        else:
            self.data[key]["qty"] = min(quantity, MAX_QTY)
        self._save()

    def remove(self, key):
        self.data.pop(key, None)
        self._save()

    def clear(self):
        self.data = {}
        self._save()

    def lines(self):
        from catalog.models import ProductPage

        ids = {v["id"] for v in self.data.values()}
        products = {p.pk: p for p in ProductPage.objects.live().filter(pk__in=ids)}
        result, stale = [], []
        for key, v in self.data.items():
            product = products.get(v["id"])
            if product is None or not product.is_available:
                stale.append(key)
                continue
            result.append(Line(key, product, v.get("size", ""), int(v.get("qty", 1))))
        if stale:  # unpublished or sold out since it was added
            for key in stale:
                del self.data[key]
            self._save()
        return result

    def __len__(self):
        return sum(int(v.get("qty", 1)) for v in self.data.values())


def cart_count(request):
    """Context processor: item count for the header."""
    if not hasattr(request, "session"):
        return {}
    return {"cart_count": len(Cart(request))}
