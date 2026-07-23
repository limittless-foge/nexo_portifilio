from .models import SiteSetting

def site_settings(request):
    return {
        'global_site_setting': SiteSetting.objects.first()
    }
