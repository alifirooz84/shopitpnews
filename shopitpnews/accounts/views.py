import json
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from listings.models import Listing
from orders.models import Order

from .forms import ProfileForm, VerificationRequestForm
from .models import OtpCode, User, VerificationRequest

PHONE_RE = re.compile(r"^09\d{9}$")


def login_page(request):
    return render(request, "accounts/login.html", {"next_url": request.GET.get("next") or "/"})


def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}


@require_POST
def request_otp(request):
    phone = _json_body(request).get("phone", "").strip()
    if not PHONE_RE.match(phone):
        return JsonResponse({"ok": False, "error": "شماره موبایل معتبر نیست."}, status=400)

    otp = OtpCode.issue(phone)
    payload = {"ok": True, "message": "کد تایید ارسال شد."}
    if settings.DEBUG:
        payload["dev_code"] = otp.code
    return JsonResponse(payload)


@require_POST
def verify_otp(request):
    data = _json_body(request)
    phone = data.get("phone", "").strip()
    code = data.get("code", "").strip()
    latest = OtpCode.objects.filter(phone=phone, used_at__isnull=True).first()
    if latest is None or not latest.verify(code):
        return JsonResponse({"ok": False, "error": "کد تایید نادرست یا منقضی شده است."}, status=400)

    user_model = get_user_model()
    user, _ = user_model.objects.get_or_create(
        phone=phone,
        defaults={"username": phone, "is_phone_verified": True},
    )
    if not user.is_phone_verified:
        user.is_phone_verified = True
        user.save(update_fields=["is_phone_verified"])
    login(request, user)
    return JsonResponse({"ok": True, "needs_profile": not bool(user.role)})


@require_POST
def save_profile(request):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "ابتدا وارد شوید."}, status=403)

    data = _json_body(request)
    role = data.get("role", "")
    valid_roles = {choice.value for choice in User.Role}
    if role not in valid_roles:
        return JsonResponse({"ok": False, "error": "نوع فعالیت معتبر نیست."}, status=400)

    request.user.role = role
    request.user.save(update_fields=["role"])
    return JsonResponse({"ok": True, "redirect": data.get("next") or "/"})


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "پروفایل شما با موفقیت ذخیره شد.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    active_listings = request.user.listings.filter(status=Listing.Status.ACTIVE)[:4]
    return render(request, "accounts/profile.html", {"form": form, "active_listings": active_listings})


def seller_profile(request, pk):
    seller = get_object_or_404(get_user_model(), pk=pk, is_active=True)
    listings = seller.listings.filter(status=Listing.Status.ACTIVE)
    completed_orders = Order.objects.filter(listing__seller=seller, status=Order.Status.DELIVERED)
    stats = {
        "active_listings": listings.count(),
        "completed_orders": completed_orders.count(),
        "total_volume": completed_orders.aggregate(total=Sum("quantity"))["total"] or 0,
        "buyers_count": completed_orders.values("buyer").distinct().count(),
    }
    return render(request, "accounts/seller_profile.html", {"seller": seller, "listings": listings, "stats": stats})


@login_required
def verification_request(request):
    latest_request = request.user.verification_requests.first()
    if request.method == "POST":
        form = VerificationRequestForm(request.POST, request.FILES)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.applicant = request.user
            verification.save()
            messages.success(request, "درخواست احراز هویت شما ثبت شد و در صف بررسی مدیر قرار گرفت.")
            return redirect("accounts:verification")
    else:
        initial = {
            "business_name": request.user.get_full_name() or request.user.username,
            "business_address": f"{request.user.province} {request.user.city}".strip(),
        }
        form = VerificationRequestForm(initial=initial)
    return render(request, "accounts/verification.html", {"form": form, "latest_request": latest_request})
