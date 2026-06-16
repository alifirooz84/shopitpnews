from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from listings.models import Listing, MarketPrice
from orders.models import Order
from payments.models import Payment

from .forms import MarketPriceForm


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
    orders = Order.objects.select_related("buyer", "listing", "listing__seller", "payment").filter(
        status=Order.Status.DISPUTED
    )
    return render(request, "backoffice/disputes.html", {"orders": orders})


@staff_member_required
def dispute_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("buyer", "listing", "listing__seller", "payment"), pk=pk
    )
    return render(request, "backoffice/dispute_detail.html", {"order": order})


@staff_member_required
@require_POST
def resolve_dispute(request, pk):
    resolution = request.POST.get("resolution")
    with transaction.atomic():
        order = get_object_or_404(
            Order.objects.select_related("payment", "listing").select_for_update(), pk=pk, status=Order.Status.DISPUTED
        )
        if resolution == "release":
            order.status = Order.Status.DELIVERED
            order.save(update_fields=["status", "updated_at"])
            order.payment.status = Payment.Status.RELEASED
            order.payment.save(update_fields=["status", "updated_at"])
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
            messages.success(request, "اختلاف به نفع خریدار بسته شد و وجه بازگشت خورد.")
        else:
            messages.error(request, "تصمیم مدیر معتبر نیست.")
            return redirect("backoffice:dispute_detail", pk=pk)
    return redirect("backoffice:disputes")
