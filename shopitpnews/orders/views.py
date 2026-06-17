from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from listings.models import Listing
from notifications.models import Notification
from notifications.services import notify_user
from payments.models import Payment

from .forms import DisputeCaseForm, DisputeMessageForm
from .models import DisputeCase, DisputeMessage, Order


def _orders_for_user(user):
    return Order.objects.select_related("listing", "listing__seller", "payment").filter(
        Q(buyer=user) | Q(listing__seller=user)
    )


def _user_can_access_dispute(user, dispute):
    return user.is_staff or dispute.order.buyer_id == user.id or dispute.order.listing.seller_id == user.id


@login_required
def order_list(request):
    purchases = request.user.orders.select_related("listing", "payment").all()
    sales = Order.objects.select_related("buyer", "listing", "payment").filter(listing__seller=request.user)
    return render(request, "orders/order_list.html", {"purchases": purchases, "sales": sales})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(_orders_for_user(request.user), pk=pk)
    dispute = getattr(order, "dispute_case", None)
    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
            "is_buyer": order.buyer_id == request.user.id,
            "is_seller": order.listing.seller_id == request.user.id,
            "dispute": dispute,
            "dispute_form": DisputeCaseForm(),
            "message_form": DisputeMessageForm(),
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

    notify_user(
        listing.seller,
        "سفارش جدید برای آگهی شما",
        f"برای آگهی {listing.title} سفارش {quantity} قطعه ثبت شد و وجه در پرداخت امن نگهداری می‌شود.",
        link_url=f"/orders/{order.pk}/",
        level=Notification.Level.SUCCESS,
        queue_sms=True,
    )
    notify_user(
        request.user,
        "سفارش شما ثبت شد",
        f"سفارش {quantity} قطعه از آگهی {listing.title} ثبت شد و وجه در پرداخت امن قرار گرفت.",
        link_url=f"/orders/{order.pk}/",
        level=Notification.Level.SUCCESS,
    )
    messages.success(request, "سفارش ثبت شد و مبلغ در وضعیت پرداخت امن قرار گرفت.")
    return redirect("orders:detail", pk=order.pk)


@login_required
@require_POST
def confirm_delivery(request, pk):
    order = get_object_or_404(request.user.orders.select_related("payment", "listing", "listing__seller"), pk=pk)
    if not order.can_confirm_delivery:
        messages.error(request, "این سفارش در وضعیت قابل تأیید تحویل نیست.")
        return redirect("orders:detail", pk=order.pk)

    order.status = Order.Status.DELIVERED
    order.save(update_fields=["status", "updated_at"])
    order.payment.status = Payment.Status.RELEASED
    order.payment.save(update_fields=["status", "updated_at"])
    settlement = order.payment.create_settlement()
    notify_user(
        order.listing.seller,
        "وجه سفارش آزاد شد",
        f"تحویل سفارش #{order.pk} تأیید شد. مبلغ خالص {settlement.net_amount if settlement else order.payment.seller_amount} تومان در دفتر تسویه ثبت شد.",
        link_url="/payments/reports/",
        level=Notification.Level.SUCCESS,
        queue_sms=True,
    )
    notify_user(request.user, "تحویل ثبت شد", f"تحویل سفارش #{order.pk} تأیید شد.", link_url=f"/orders/{order.pk}/", level=Notification.Level.SUCCESS)
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

    notify_user(order.listing.seller, "سفارش لغو شد", f"سفارش #{order.pk} لغو شد و موجودی به آگهی برگشت.", link_url=f"/orders/{order.pk}/", level=Notification.Level.WARNING)
    notify_user(request.user, "بازگشت وجه ثبت شد", f"سفارش #{order.pk} لغو شد و وجه در وضعیت بازگشت قرار گرفت.", link_url=f"/orders/{order.pk}/", level=Notification.Level.WARNING)
    messages.success(request, "سفارش لغو شد و وجه در وضعیت بازگشت قرار گرفت.")
    return redirect("orders:detail", pk=order.pk)


@login_required
@require_POST
def report_dispute(request, pk):
    order = get_object_or_404(_orders_for_user(request.user).select_related("payment", "listing", "listing__seller"), pk=pk)
    if not order.can_be_disputed and order.status != Order.Status.DISPUTED:
        messages.error(request, "برای این سفارش امکان ثبت اختلاف وجود ندارد.")
        return redirect("orders:detail", pk=order.pk)

    dispute = getattr(order, "dispute_case", None)
    if dispute is not None:
        messages.warning(request, "برای این سفارش قبلاً پرونده اختلاف ثبت شده است.")
        return redirect("orders:detail", pk=order.pk)

    form = DisputeCaseForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "اطلاعات اختلاف کامل نیست.")
        return redirect("orders:detail", pk=order.pk)

    with transaction.atomic():
        dispute = form.save(commit=False)
        dispute.order = order
        dispute.opened_by = request.user
        if not dispute.description:
            dispute.description = "اختلاف بدون توضیح تکمیلی ثبت شد."
        dispute.save()
        DisputeMessage.objects.create(
            dispute=dispute,
            author=request.user,
            body=dispute.description,
            attachment=dispute.evidence,
        )
        order.status = Order.Status.DISPUTED
        order.save(update_fields=["status", "updated_at"])
        order.payment.status = Payment.Status.HELD
        order.payment.save(update_fields=["status", "updated_at"])

    other_party = order.listing.seller if request.user == order.buyer else order.buyer
    notify_user(other_party, "اختلاف برای سفارش ثبت شد", f"برای سفارش #{order.pk} اختلاف ثبت شد و وجه تا تصمیم مدیر نگهداری می‌شود.", link_url=f"/orders/{order.pk}/", level=Notification.Level.WARNING, queue_sms=True)
    notify_user(request.user, "اختلاف شما ثبت شد", f"اختلاف سفارش #{order.pk} ثبت شد و مدیر آن را بررسی می‌کند.", link_url=f"/orders/{order.pk}/", level=Notification.Level.WARNING)
    messages.warning(request, "اختلاف ثبت شد. وجه تا تصمیم مدیر نزد سامانه نگهداری می‌شود.")
    return redirect("orders:detail", pk=order.pk)


@login_required
@require_POST
def add_dispute_message(request, pk):
    dispute = get_object_or_404(DisputeCase.objects.select_related("order", "order__listing"), pk=pk)
    if not _user_can_access_dispute(request.user, dispute):
        messages.error(request, "دسترسی به این پرونده اختلاف مجاز نیست.")
        return redirect("orders:list")
    if dispute.status != DisputeCase.Status.OPEN:
        messages.error(request, "پرونده مختومه قابل افزودن پیام نیست.")
        return redirect("orders:detail", pk=dispute.order_id)
    form = DisputeMessageForm(request.POST, request.FILES)
    if form.is_valid():
        message = form.save(commit=False)
        message.dispute = dispute
        message.author = request.user
        message.is_staff_note = request.user.is_staff
        message.save()
        recipient = dispute.order.buyer if request.user == dispute.order.listing.seller else dispute.order.listing.seller
        if request.user.is_staff:
            notify_user(dispute.order.buyer, "پیام مدیر در پرونده اختلاف", f"برای سفارش #{dispute.order_id} پیام جدید ثبت شد.", link_url=f"/orders/{dispute.order_id}/", level=Notification.Level.INFO)
            notify_user(dispute.order.listing.seller, "پیام مدیر در پرونده اختلاف", f"برای سفارش #{dispute.order_id} پیام جدید ثبت شد.", link_url=f"/orders/{dispute.order_id}/", level=Notification.Level.INFO)
        else:
            notify_user(recipient, "پیام جدید در پرونده اختلاف", f"برای سفارش #{dispute.order_id} پیام جدید ثبت شد.", link_url=f"/orders/{dispute.order_id}/", level=Notification.Level.INFO)
        messages.success(request, "پیام پرونده اختلاف ثبت شد.")
    else:
        messages.error(request, "متن پیام معتبر نیست.")
    return redirect("orders:detail", pk=dispute.order_id)
