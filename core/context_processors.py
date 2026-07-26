from .models import SiteSetting

def site_settings(request):
    setting = SiteSetting.objects.first()
    return {
        'global_site_setting': setting,
        'site_settings': setting
    }
