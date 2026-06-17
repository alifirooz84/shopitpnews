from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from listings.models import Listing
from orders.models import Order
from notifications.models import Notification
from notifications.services import notify_user

from .forms import ConversationMessageForm, ReviewForm
from .models import Conversation, ConversationMessage, FavoriteListing, Review


@login_required
def favorites(request):
    favorites_qs = request.user.favorite_listings.select_related("listing", "listing__seller")
    return render(request, "engagement/favorites.html", {"favorites": favorites_qs})


@login_required
@require_POST
def toggle_favorite(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    favorite = FavoriteListing.objects.filter(user=request.user, listing=listing).first()
    if favorite:
        favorite.delete()
        messages.success(request, "آگهی از علاقه‌مندی‌ها حذف شد.")
    else:
        FavoriteListing.objects.create(user=request.user, listing=listing)
        messages.success(request, "آگهی به علاقه‌مندی‌ها اضافه شد.")
    return redirect(request.POST.get("next") or listing.get_absolute_url())


@login_required
def conversations(request):
    conversations_qs = Conversation.visible_to(request.user).prefetch_related("messages")
    return render(request, "engagement/conversations.html", {"conversations": conversations_qs})


@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(Conversation.visible_to(request.user), pk=pk)
    conversation.messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)
    return render(
        request,
        "engagement/conversation_detail.html",
        {"conversation": conversation, "form": ConversationMessageForm()},
    )


def _conversation_recipient(conversation, sender):
    return conversation.seller if sender == conversation.buyer else conversation.buyer


@login_required
@require_POST
def contact_seller(request, listing_id):
    listing = get_object_or_404(Listing.objects.select_related("seller"), pk=listing_id)
    if listing.seller_id == request.user.id:
        messages.error(request, "برای آگهی خودتان امکان شروع گفت‌وگو وجود ندارد.")
        return redirect(listing.get_absolute_url())
    conversation, _ = Conversation.objects.get_or_create(
        listing=listing,
        buyer=request.user,
        seller=listing.seller,
    )
    body = request.POST.get("body", "").strip() or f"سلام، درباره آگهی {listing.title} سوال دارم."
    message = ConversationMessage.objects.create(conversation=conversation, sender=request.user, body=body)
    conversation.save(update_fields=["updated_at"])
    notify_user(
        listing.seller,
        "پیام جدید درباره آگهی",
        f"برای آگهی {listing.title} پیام جدیدی دریافت کردید.",
        link_url=conversation.get_absolute_url(),
        level=Notification.Level.INFO,
        queue_sms=True,
    )
    messages.success(request, "گفت‌وگو با فروشنده شروع شد.")
    return redirect(conversation.get_absolute_url())


@login_required
@require_POST
def add_message(request, pk):
    conversation = get_object_or_404(Conversation.visible_to(request.user), pk=pk)
    form = ConversationMessageForm(request.POST, request.FILES)
    if form.is_valid():
        message = form.save(commit=False)
        message.conversation = conversation
        message.sender = request.user
        message.save()
        conversation.save(update_fields=["updated_at"])
        recipient = _conversation_recipient(conversation, request.user)
        notify_user(
            recipient,
            "پیام جدید در گفت‌وگو",
            f"در گفت‌وگوی آگهی {conversation.listing.title} پیام جدیدی دارید.",
            link_url=conversation.get_absolute_url(),
            level=Notification.Level.INFO,
        )
        messages.success(request, "پیام ارسال شد.")
    else:
        messages.error(request, "متن پیام معتبر نیست.")
    return redirect(conversation.get_absolute_url())


@login_required
@require_POST
def create_review(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("listing", "listing__seller"),
        pk=order_id,
        buyer=request.user,
        status=Order.Status.DELIVERED,
    )
    if hasattr(order, "review"):
        messages.warning(request, "برای این سفارش قبلاً نظر ثبت کرده‌اید.")
        return redirect("orders:detail", pk=order.pk)
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.order = order
        review.reviewer = request.user
        review.seller = order.listing.seller
        review.save()
        notify_user(
            review.seller,
            "نظر جدید برای معامله",
            f"خریدار سفارش #{order.pk} برای شما امتیاز {review.rating} ثبت کرد.",
            link_url=f"/accounts/sellers/{review.seller_id}/",
            level=Notification.Level.SUCCESS,
        )
        messages.success(request, "نظر شما برای فروشنده ثبت شد.")
    else:
        messages.error(request, "امتیاز یا متن نظر معتبر نیست.")
    return redirect("orders:detail", pk=order.pk)
