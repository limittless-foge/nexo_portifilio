from django.test import TestCase

from .context_processors import site_settings as site_settings_context_processor
from .models import SiteSetting


class SiteSettingTests(TestCase):
    def test_get_instance_creates_and_reuses_singleton(self):
        setting = SiteSetting.get_instance()

        self.assertIsInstance(setting, SiteSetting)
        self.assertEqual(setting.education_external_url, "https://example.com")
        self.assertEqual(setting.header_phone_number, "+251 968 929 372")
        self.assertEqual(SiteSetting.objects.count(), 1)

        same_setting = SiteSetting.get_instance()
        self.assertEqual(same_setting.pk, setting.pk)

    def test_context_processor_includes_site_settings(self):
        context = site_settings_context_processor(type("Request", (), {})())

        self.assertIsNotNone(context["site_settings"])
        self.assertEqual(context["site_settings"], SiteSetting.get_instance())
