from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import ProductPage

from .cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem
from .notifications import notify_new_order


@require_POST
def cart_add(request):
    product = get_object_or_404(ProductPage.objects.live(), pk=request.POST.get("product"))
    size = request.POST.get("size", "").strip()
    sizes = product.size_list
    if not product.is_available:
        return redirect(product.url)
    if sizes and size not in sizes:
        return redirect(product.url + "?need_size=1#buy")
    if not sizes:
        size = ""
    Cart(request).add(product, size)
    return redirect(product.url + "?added=1#buy")


@require_POST
def cart_update(request):
    cart = Cart(request)
    key = request.POST.get("key", "")
    if "remove" in request.POST:
        cart.remove(key)
    else:
        try:
            cart.set_quantity(key, int(request.POST.get("qty", 1)))
        except ValueError:
            pass
    return redirect("cart")


def cart_view(request):
    cart = Cart(request)
    lines = cart.lines()
    form = CheckoutForm(request.POST or None)

    if request.method == "POST" and lines and form.is_valid():
        total = sum(line.total for line in lines)
        summary = ", ".join(
            f"{l.product.title}{f' ({l.size})' if l.size else ''} ×{l.quantity}" for l in lines)
        with transaction.atomic():
            order = form.save(commit=False)
            order.product_title = summary[:255]
            order.price = total
            if len(lines) == 1:
                order.product, order.size = lines[0].product, lines[0].size
            order.save()
            OrderItem.objects.bulk_create([
                OrderItem(order=order, product=l.product, title=l.product.title, size=l.size,
                          quantity=l.quantity, price=l.product.price, sort_order=i)
                for i, l in enumerate(lines)
            ])
            transaction.on_commit(lambda: notify_new_order(order))
        cart.clear()
        request.session["last_order"] = order.pk
        return redirect("cart_done")

    return render(request, "orders/cart.html", {
        "lines": lines,
        "total": sum(line.total for line in lines),
        "form": form,
    })


def cart_done(request):
    order = Order.objects.filter(pk=request.session.get("last_order")).first()
    if order is None:
        return redirect("cart")
    return render(request, "orders/done.html", {"order": order})
