from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from listings.models import Listing
from payments.models import Payment

from .models import Order


@login_required
def order_list(request):
    orders = request.user.orders.select_related("listing", "payment")
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
@require_POST
def create_order(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id, status=Listing.Status.ACTIVE)
    order_type = request.POST.get("order_type", Order.OrderType.INSTANT)
    if order_type not in {choice.value for choice in Order.OrderType}:
        order_type = Order.OrderType.INSTANT

    requested_quantity = int(request.POST.get("quantity") or 1)
    quantity = max(1, min(requested_quantity, listing.quantity))
    total_amount = quantity * listing.price_per_chick
    order = Order.objects.create(
        buyer=request.user,
        listing=listing,
        order_type=order_type,
        quantity=quantity,
        unit_price=listing.price_per_chick,
        total_amount=total_amount,
    )
    Payment.objects.create(order=order, amount=total_amount)
    messages.success(request, "سفارش ثبت شد و مبلغ در وضعیت پرداخت امن قرار گرفت.")
    return redirect("orders:list")
