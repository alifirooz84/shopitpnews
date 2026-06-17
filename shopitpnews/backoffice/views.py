import csv

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from listings.models import Listing, MarketPrice
from orders.forms import DisputeMessageForm
from orders.models import DisputeCase, DisputeMessage, Order
from payments.models import Payment, Settlement
from notifications.models import MessageOutbox
from notifications.services import broadcast_newsletter, notify_user

from .forms import MarketPriceForm, NewsletterForm


@staff_member_required
def overview(request):
    context = {
        "users_count": get_user_model().objects.count(),
        "active_listings_count": Listing.objects.filter(status=Listing.Status.ACTIVE).count(),
        "orders_count": Order.objects.count(),
        "disputes_count": Order.objects.filter(status=Order.Status.DISPUTED).count(),
        "held_amount": Payment.objects.filter(status=Payment.Status.HELD).aggregate(total=Sum("amount"))["total"] or 0,
        "market_prices": MarketPrice.objects.all(),
        "recent_orders": Order.objects.select_related("buyer", "listing", "payment")[:6],
        "disputed_orders": Order.objects.select_related("buyer", "listing", "payment").filter(status=Order.Status.DISPUTED)[:6],
    }
    return render(request, "backoffice/overview.html", context)


@staff_member_required
def market_prices(request):
    price_id = request.POST.get("price_id") if request.method == "POST" else None
    instance = MarketPrice.objects.filter(pk=price_id).first() if price_id else None
    form = MarketPriceForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "قیمت بازار ذخیره شد.")
        return redirect("backoffice:market_prices")

    return render(
        request,
        "backoffice/market_prices.html",
        {"form": form, "market_prices": MarketPrice.objects.all()},
    )


@staff_member_required
@require_POST
def delete_market_price(request, pk):
    get_object_or_404(MarketPrice, pk=pk).delete()
    messages.success(request, "شاخص قیمت حذف شد.")
    return redirect("backoffice:market_prices")


@staff_member_required
def users(request):
    user_model = get_user_model()
    query = request.GET.get("q", "").strip()
    users_qs = user_model.objects.annotate(
        listings_count=Count("listings", distinct=True),
        orders_count=Count("orders", distinct=True),
    ).order_by("-date_joined")
    if query:
        users_qs = users_qs.filter(
            Q(username__icontains=query)
            | Q(phone__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )
    return render(request, "backoffice/users.html", {"users": users_qs, "query": query})


@staff_member_required
@require_POST
def user_action(request, pk):
    user = get_object_or_404(get_user_model(), pk=pk)
    action = request.POST.get("action")
    if action == "verify":
        user.is_phone_verified = True
        user.save(update_fields=["is_phone_verified"])
        messages.success(request, "کاربر تأیید شد.")
    elif action == "suspend" and not user.is_staff:
        user.is_active = False
        user.save(update_fields=["is_active"])
        messages.warning(request, "کاربر تعلیق شد.")
    elif action == "activate":
        user.is_active = True
        user.save(update_fields=["is_active"])
        messages.success(request, "کاربر فعال شد.")
    else:
        messages.error(request, "عملیات معتبر نیست.")
    return redirect("backoffice:users")


@staff_member_required
def disputes(request):
    cases = DisputeCase.objects.select_related(
        "order", "order__buyer", "order__listing", "order__listing__seller", "order__payment", "opened_by"
    ).filter(status=DisputeCase.Status.OPEN)
    return render(request, "backoffice/disputes.html", {"cases": cases})


@staff_member_required
def dispute_detail(request, pk):
    dispute = get_object_or_404(
        DisputeCase.objects.select_related(
            "order", "order__buyer", "order__listing", "order__listing__seller", "order__payment", "opened_by"
        ).prefetch_related("messages", "messages__author"),
        pk=pk,
    )
    return render(request, "backoffice/dispute_detail.html", {"dispute": dispute, "order": dispute.order, "message_form": DisputeMessageForm()})


@staff_member_required
@require_POST
def add_dispute_message(request, pk):
    dispute = get_object_or_404(DisputeCase.objects.select_related("order"), pk=pk, status=DisputeCase.Status.OPEN)
    form = DisputeMessageForm(request.POST, request.FILES)
    if form.is_valid():
        message = form.save(commit=False)
        message.dispute = dispute
        message.author = request.user
        message.is_staff_note = True
        message.save()
        notify_user(dispute.order.buyer, "پیام مدیر در پرونده اختلاف", f"برای سفارش #{dispute.order_id} پیام جدید ثبت شد.", link_url=f"/orders/{dispute.order_id}/", level="info")
        notify_user(dispute.order.listing.seller, "پیام مدیر در پرونده اختلاف", f"برای سفارش #{dispute.order_id} پیام جدید ثبت شد.", link_url=f"/orders/{dispute.order_id}/", level="info")
        messages.success(request, "پیام مدیر ثبت شد.")
    else:
        messages.error(request, "متن پیام معتبر نیست.")
    return redirect("backoffice:dispute_detail", pk=pk)


@staff_member_required
@require_POST
def resolve_dispute(request, pk):
    resolution = request.POST.get("resolution")
    resolution_note = request.POST.get("resolution_note", "").strip()
    with transaction.atomic():
        dispute = get_object_or_404(
            DisputeCase.objects.select_related("order", "order__payment", "order__listing").select_for_update(),
            pk=pk,
            status=DisputeCase.Status.OPEN,
        )
        order = dispute.order
        if resolution == "release":
            order.status = Order.Status.DELIVERED
            order.save(update_fields=["status", "updated_at"])
            order.payment.status = Payment.Status.RELEASED
            order.payment.save(update_fields=["status", "updated_at"])
            settlement = order.payment.create_settlement()
            dispute.status = DisputeCase.Status.RELEASED
            dispute.resolved_by = request.user
            dispute.resolution_note = resolution_note or "اختلاف به نفع فروشنده بسته شد و وجه آزاد شد."
            from django.utils import timezone
            dispute.resolved_at = timezone.now()
            dispute.save(update_fields=["status", "resolved_by", "resolution_note", "resolved_at", "updated_at"])
            DisputeMessage.objects.create(dispute=dispute, author=request.user, body=dispute.resolution_note, is_staff_note=True)
            notify_user(order.listing.seller, "اختلاف به نفع شما بسته شد", f"وجه سفارش #{order.pk} آزاد شد و مبلغ خالص {settlement.net_amount if settlement else order.payment.seller_amount} تومان در دفتر تسویه ثبت شد.", link_url="/payments/reports/", level="success", queue_sms=True)
            notify_user(order.buyer, "اختلاف سفارش بسته شد", f"اختلاف سفارش #{order.pk} بررسی و وجه برای فروشنده آزاد شد.", link_url=f"/orders/{order.pk}/", level="info")
            messages.success(request, "اختلاف به نفع فروشنده بسته شد و وجه آزاد شد.")
        elif resolution == "refund":
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
            dispute.status = DisputeCase.Status.REFUNDED
            dispute.resolved_by = request.user
            dispute.resolution_note = resolution_note or "اختلاف به نفع خریدار بسته شد و وجه بازگشت خورد."
            from django.utils import timezone
            dispute.resolved_at = timezone.now()
            dispute.save(update_fields=["status", "resolved_by", "resolution_note", "resolved_at", "updated_at"])
            DisputeMessage.objects.create(dispute=dispute, author=request.user, body=dispute.resolution_note, is_staff_note=True)
            notify_user(order.buyer, "اختلاف به نفع شما بسته شد", f"وجه سفارش #{order.pk} در وضعیت بازگشت قرار گرفت.", link_url=f"/orders/{order.pk}/", level="success", queue_sms=True)
            notify_user(order.listing.seller, "اختلاف سفارش بسته شد", f"اختلاف سفارش #{order.pk} به بازگشت وجه منجر شد.", link_url=f"/orders/{order.pk}/", level="warning")
            messages.success(request, "اختلاف به نفع خریدار بسته شد و وجه بازگشت خورد.")
        else:
            messages.error(request, "تصمیم مدیر معتبر نیست.")
            return redirect("backoffice:dispute_detail", pk=pk)
    return redirect("backoffice:disputes")


@staff_member_required
def financial_reports(request):
    payments = Payment.objects.select_related("order", "order__buyer", "order__listing", "order__listing__seller")
    settlements = Settlement.objects.select_related("seller", "payment", "payment__order", "payment__order__listing")
    context = {
        "payments": payments[:50],
        "settlements": settlements[:50],
        "held_total": payments.filter(status=Payment.Status.HELD).aggregate(total=Sum("amount"))["total"] or 0,
        "released_total": payments.filter(status=Payment.Status.RELEASED).aggregate(total=Sum("amount"))["total"] or 0,
        "refunded_total": payments.filter(status=Payment.Status.REFUNDED).aggregate(total=Sum("amount"))["total"] or 0,
        "commission_total": sum(payment.commission_amount for payment in payments.filter(status=Payment.Status.RELEASED)),
        "pending_settlement_total": settlements.filter(status=Settlement.Status.PENDING).aggregate(total=Sum("net_amount"))["total"] or 0,
        "paid_settlement_total": settlements.filter(status=Settlement.Status.PAID).aggregate(total=Sum("net_amount"))["total"] or 0,
    }
    return render(request, "backoffice/financial_reports.html", context)


@staff_member_required
def financial_reports_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="platform-financial-report.csv"'
    response.write("﻿")
    writer = csv.writer(response)
    writer.writerow(["settlement_id", "order_id", "seller", "listing", "gross", "commission", "net", "status", "created_at", "paid_at"])
    for settlement in Settlement.objects.select_related("seller", "payment", "payment__order", "payment__order__listing"):
        writer.writerow([
            settlement.id,
            settlement.payment.order_id,
            settlement.seller.phone or settlement.seller.username,
            settlement.payment.order.listing.title,
            settlement.gross_amount,
            settlement.commission_amount,
            settlement.net_amount,
            settlement.get_status_display(),
            settlement.created_at.isoformat(),
            settlement.paid_at.isoformat() if settlement.paid_at else "",
        ])
    return response


@staff_member_required
@require_POST
def mark_settlement_paid(request, pk):
    settlement = get_object_or_404(Settlement, pk=pk, status=Settlement.Status.PENDING)
    settlement.mark_paid(notes=request.POST.get("notes", ""))
    notify_user(settlement.seller, "تسویه واریز شد", f"تسویه سفارش #{settlement.payment.order_id} به مبلغ {settlement.net_amount} تومان به عنوان واریز شده ثبت شد.", link_url="/payments/reports/", level="success", queue_sms=True)
    messages.success(request, "تسویه به عنوان واریز شده ثبت شد.")
    return redirect("backoffice:financial_reports")


@staff_member_required
def newsletters(request):
    form = NewsletterForm(request.POST or None)
    user_model = get_user_model()
    if request.method == "POST" and form.is_valid():
        target = form.cleaned_data["target"]
        users = user_model.objects.filter(is_active=True)
        if target == NewsletterForm.Target.VERIFIED:
            users = users.filter(is_phone_verified=True)
        elif target == NewsletterForm.Target.SELLERS:
            users = users.filter(listings__isnull=False).distinct()
        elif target == NewsletterForm.Target.BUYERS:
            users = users.filter(orders__isnull=False).distinct()
        count = broadcast_newsletter(users, form.cleaned_data["title"], form.cleaned_data["body"])
        if form.cleaned_data["queue_sms"]:
            for user in users.exclude(phone__exact=""):
                MessageOutbox.objects.create(
                    recipient=user,
                    recipient_phone=user.phone,
                    channel=MessageOutbox.Channel.SMS,
                    subject=form.cleaned_data["title"],
                    body=form.cleaned_data["body"],
                )
        messages.success(request, f"خبرنامه برای {count} کاربر ثبت شد.")
        return redirect("backoffice:newsletters")
    outbox = MessageOutbox.objects.select_related("recipient")[:50]
    return render(request, "backoffice/newsletters.html", {"form": form, "outbox": outbox})
