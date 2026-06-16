from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    unread_count = notifications.filter(is_read=False).count()
    return render(request, "notifications/list.html", {"notifications": notifications, "unread_count": unread_count})


@login_required
@require_POST
def mark_read(request, pk):
    notification = get_object_or_404(request.user.notifications, pk=pk)
    notification.mark_read()
    if notification.link_url:
        return redirect(notification.link_url)
    return redirect("notifications:list")


@login_required
@require_POST
def mark_all_read(request):
    for notification in request.user.notifications.filter(is_read=False):
        notification.mark_read()
    messages.success(request, "همه اعلان‌ها خوانده شد.")
    return redirect("notifications:list")
