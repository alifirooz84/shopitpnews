from .models import MessageOutbox, Notification


def notify_user(user, title, body, *, link_url="", level=Notification.Level.INFO, queue_sms=False):
    if not user or not getattr(user, "is_active", True):
        return None
    notification = Notification.objects.create(
        recipient=user,
        title=title,
        body=body,
        link_url=link_url,
        level=level,
    )
    MessageOutbox.objects.create(
        recipient=user,
        recipient_phone=getattr(user, "phone", "") or "",
        channel=MessageOutbox.Channel.SYSTEM,
        subject=title,
        body=body,
        status=MessageOutbox.Status.SENT,
    )
    if queue_sms and getattr(user, "phone", ""):
        MessageOutbox.objects.create(
            recipient=user,
            recipient_phone=user.phone,
            channel=MessageOutbox.Channel.SMS,
            subject=title,
            body=body,
        )
    return notification


def broadcast_newsletter(users, title, body):
    count = 0
    for user in users:
        notify_user(user, title, body, level=Notification.Level.INFO)
        MessageOutbox.objects.create(
            recipient=user,
            recipient_phone=getattr(user, "phone", "") or "",
            channel=MessageOutbox.Channel.NEWSLETTER,
            subject=title,
            body=body,
        )
        count += 1
    return count
