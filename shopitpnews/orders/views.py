from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from listings.models import Listing
from payments.models import Payment

from .models import Order


def _orders_for_user(user):
    return Order.objects.select_related("listing", "listing__seller", "payment").filter(
        Q(buyer=user) | Q(listing__seller=user)
    )


@login_required
def order_list(request):
    purchases = request.user.orders.select_related("listing", "payment").all()
    sales = Order.objects.select_related("buyer", "listing", "payment").filter(listing__seller=request.user)
    return render(request, "orders/order_list.html", {"purchases": purchases, "sales": sales})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(_orders_for_user(request.user), pk=pk)
    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
            "is_buyer": order.buyer_id == request.user.id,
            "is_seller": order.listing.seller_id == request.user.id,
        },
    )


@login_required
@require_POST
def create_order(request, listing_id):
    order_type = request.POST.get("order_type", Order.OrderType.INSTANT)
    if order_type not in {choice.value for choice in Order.OrderType}:
        order_type = Order.OrderType.INSTANT

    try:
        requested_quantity = int(request.POST.get("quantity") or 1)
    except (TypeError, ValueError):
        requested_quantity = 1

    with transaction.atomic():
        listing = get_object_or_404(
            Listing.objects.select_for_update(), pk=listing_id, status=Listing.Status.ACTIVE
        )
        if listing.seller_id == request.user.id:
            messages.error(request, "امکان ثبت سفارش برای آگهی خودتان وجود ندارد.")
            return redirect(listing.get_absolute_url())
        if listing.quantity < 1:
            messages.error(request, "موجودی این آگهی به پایان رسیده است.")
            return redirect(listing.get_absolute_url())

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

        listing.quantity -= quantity
        if listing.quantity == 0:
            listing.status = Listing.Status.SOLD
            listing.reservation_percent = 100
        else:
            listing.reservation_percent = min(99, listing.reservation_percent + 10)
        listing.save(update_fields=["quantity", "status", "reservation_percent", "updated_at"])

    messages.success(request, "سفارش ثبت شد و مبلغ در وضعیت پرداخت امن قرار گرفت.")
    return redirect("orders:detail", pk=order.pk)


@login_required
@require_POST
def confirm_delivery(request, pk):
    order = get_object_or_404(request.user.orders.select_related("payment"), pk=pk)
    if not order.can_confirm_delivery:
        messages.error(request, "این سفارش در وضعیت قابل تأیید تحویل نیست.")
        return redirect("orders:detail", pk=order.pk)

    order.status = Order.Status.DELIVERED
    order.save(update_fields=["status", "updated_at"])
    order.payment.status = Payment.Status.RELEASED
    order.payment.save(update_fields=["status", "updated_at"])
    order.payment.create_settlement()
    messages.success(request, "تحویل تأیید شد و وجه پس از کسر کارمزد برای فروشنده آزاد شد.")
    return redirect("orders:detail", pk=order.pk)


@login_required
@require_POST
def cancel_order(request, pk):
    order = get_object_or_404(request.user.orders.select_related("listing", "payment"), pk=pk)
    if not order.can_be_cancelled:
        messages.error(request, "این سفارش قابل لغو نیست.")
        return redirect("orders:detail", pk=order.pk)

    with transaction.atomic():
        listing = Listing.objects.select_for_update().get(pk=order.listing_id)
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        order.payment.status = Payment.Status.REFUNDED
        order.payment.save(update_fields=["status", "updated_at"])
        listing.quantity += order.quantity
        if listing.status == Listing.Status.SOLD:
            listing.status = Listing.Status.ACTIVE
        listing.reservation_percent = max(0, listing.reservation_percent - 10)
        listing.save(update_fields=["quantity", "status", "reservation_percent", "updated_at"])

    messages.success(request, "سفارش لغو شد و وجه در وضعیت بازگشت قرار گرفت.")
    return redirect("orders:detail", pk=order.pk)


@login_required
@require_POST
def report_dispute(request, pk):
    order = get_object_or_404(_orders_for_user(request.user).select_related("payment"), pk=pk)
    if not order.can_be_disputed:
        messages.error(request, "برای این سفارش امکان ثبت اختلاف وجود ندارد.")
        return redirect("orders:detail", pk=order.pk)

    order.status = Order.Status.DISPUTED
    order.save(update_fields=["status", "updated_at"])
    order.payment.status = Payment.Status.HELD
    order.payment.save(update_fields=["status", "updated_at"])
    messages.warning(request, "اختلاف ثبت شد. وجه تا تصمیم مدیر نزد سامانه نگهداری می‌شود.")
    return redirect("orders:detail", pk=order.pk)
