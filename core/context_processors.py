from .models import SiteSetting


def site_settings(request):
    """Expose the shared SiteSetting instance to all templates."""
    setting, _ = SiteSetting.objects.get_or_create(id=1)
    return {
        'site_setting': setting,
        'site_settings': setting,
        'global_site_setting': setting,
    }


def notifications_context(request):
    """Expose unread_notifications_count globally to all templates."""
    if request.user and request.user.is_authenticated:
        from .models import Notification
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    else:
        count = 0
    return {
        'unread_notifications_count': count
    }
