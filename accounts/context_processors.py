from .models import Notification


def notification_context(request):
    if not request.user.is_authenticated:
        return {}
    return {
        'unread_notifications': Notification.objects.filter(recipient=request.user, is_read=False).count(),
        'latest_notifications': Notification.objects.filter(recipient=request.user)[:5],
    }