import csv

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from .models import Payment, Settlement


def health(request):
    return JsonResponse({"ok": True, "module": "payments"})


@login_required
def financial_report(request):
    purchase_payments = Payment.objects.select_related("order", "order__listing").filter(order__buyer=request.user)
    sales_payments = Payment.objects.select_related("order", "order__listing", "settlement").filter(order__listing__seller=request.user)
    settlements = Settlement.objects.select_related("payment", "payment__order", "payment__order__listing").filter(seller=request.user)
    context = {
        "purchase_payments": purchase_payments,
        "sales_payments": sales_payments,
        "settlements": settlements,
        "purchase_total": purchase_payments.aggregate(total=Sum("amount"))["total"] or 0,
        "held_total": sales_payments.filter(status=Payment.Status.HELD).aggregate(total=Sum("amount"))["total"] or 0,
        "released_total": settlements.aggregate(total=Sum("net_amount"))["total"] or 0,
        "paid_total": settlements.filter(status=Settlement.Status.PAID).aggregate(total=Sum("net_amount"))["total"] or 0,
    }
    return render(request, "payments/financial_report.html", context)


@login_required
def financial_report_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="financial-report.csv"'
    response.write("﻿")
    writer = csv.writer(response)
    writer.writerow(["type", "order_id", "listing", "gross_amount", "commission", "net_amount", "status", "created_at"])
    for payment in Payment.objects.select_related("order", "order__listing").filter(order__buyer=request.user):
        writer.writerow([
            "purchase",
            payment.order_id,
            payment.order.listing.title,
            payment.amount,
            payment.commission_amount,
            payment.seller_amount,
            payment.get_status_display(),
            payment.created_at.isoformat(),
        ])
    for settlement in Settlement.objects.select_related("payment", "payment__order", "payment__order__listing").filter(seller=request.user):
        writer.writerow([
            "settlement",
            settlement.payment.order_id,
            settlement.payment.order.listing.title,
            settlement.gross_amount,
            settlement.commission_amount,
            settlement.net_amount,
            settlement.get_status_display(),
            settlement.created_at.isoformat(),
        ])
    return response
