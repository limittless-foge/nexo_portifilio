from .models import SiteSetting


def site_settings(request):
    """Expose the shared SiteSetting instance to all templates."""
    setting, _ = SiteSetting.objects.get_or_create(id=1)
    return {
        'site_setting': setting,
        'site_settings': setting,
        'global_site_setting': setting,
    }
