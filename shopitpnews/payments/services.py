from django.db import transaction

from .models import Payment, Wallet, WalletTransaction


def get_wallet(user):
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


@transaction.atomic
def credit_wallet(user, amount, *, transaction_type, description="", payment=None):
    wallet = Wallet.objects.select_for_update().get_or_create(user=user)[0]
    wallet.balance += amount
    wallet.save(update_fields=["balance", "updated_at"])
    return WalletTransaction.objects.create(
        wallet=wallet,
        payment=payment,
        transaction_type=transaction_type,
        amount=amount,
        balance_after=wallet.balance,
        description=description,
    )


def top_up_wallet(user, amount, description="شارژ توسعه‌ای کیف پول"):
    return credit_wallet(
        user,
        amount,
        transaction_type=WalletTransaction.TransactionType.TOP_UP,
        description=description,
    )


def credit_refund(payment):
    if payment.status != Payment.Status.REFUNDED:
        return None
    existing = WalletTransaction.objects.filter(
        payment=payment,
        transaction_type=WalletTransaction.TransactionType.REFUND,
    ).first()
    if existing:
        return existing
    return credit_wallet(
        payment.order.buyer,
        payment.amount,
        transaction_type=WalletTransaction.TransactionType.REFUND,
        description=f"بازگشت وجه سفارش #{payment.order_id}",
        payment=payment,
    )
