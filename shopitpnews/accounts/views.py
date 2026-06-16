import json
import re

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import OtpCode, User

PHONE_RE = re.compile(r"^09\d{9}$")


def login_page(request):
    return render(request, "accounts/login.html")


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

    role = _json_body(request).get("role", "")
    valid_roles = {choice.value for choice in User.Role}
    if role not in valid_roles:
        return JsonResponse({"ok": False, "error": "نوع فعالیت معتبر نیست."}, status=400)

    request.user.role = role
    request.user.save(update_fields=["role"])
    return JsonResponse({"ok": True, "redirect": "/"})


def profile(request):
    return render(request, "accounts/profile.html")
