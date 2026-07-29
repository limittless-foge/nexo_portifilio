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


from django.contrib.auth.models import User
from django.urls import reverse
from .models import ClientProfile, RoadmapStep, create_default_roadmap_steps

class RoadmapTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testclient', password='password123')
        # Profile is auto-created by signal on User creation
        self.profile = ClientProfile.objects.get(user=self.user)
        self.client.login(username='testclient', password='password123')

    def test_default_steps_seeded_if_none_exist(self):
        # Delete steps that might be created by signal
        RoadmapStep.objects.filter(client=self.user).delete()
        self.assertEqual(RoadmapStep.objects.filter(client=self.user).count(), 0)

        # Access client dashboard
        response = self.client.get(reverse('client_dashboard'))
        self.assertEqual(response.status_code, 200)

        # Check that 4 steps exist and are DECLINED
        steps = RoadmapStep.objects.filter(client=self.user).order_by('order')
        self.assertEqual(steps.count(), 4)
        for step in steps:
            self.assertEqual(step.status, 'DECLINED')
        
        # Verify accurate progress percent in context
        self.assertEqual(response.context['progress_percent'], 0)

    def test_progress_percent_calculations(self):
        # Delete all steps and create exactly 4 steps
        RoadmapStep.objects.filter(client=self.user).delete()
        create_default_roadmap_steps(self.user)
        steps = list(RoadmapStep.objects.filter(client=self.user).order_by('order'))
        
        # Verify 0 approved steps = 0%
        self.assertEqual(self.profile.onboarding_progress_percentage, 0)
        self.assertFalse(self.profile.all_milestones_approved)

        # Approve 1 step
        steps[0].status = 'APPROVED'
        steps[0].save()
        self.assertEqual(self.profile.onboarding_progress_percentage, 25)
        self.assertFalse(self.profile.all_milestones_approved)

        # Approve 2 steps
        steps[1].status = 'APPROVED'
        steps[1].save()
        self.assertEqual(self.profile.onboarding_progress_percentage, 50)
        self.assertFalse(self.profile.all_milestones_approved)

        # Approve 3 steps
        steps[2].status = 'APPROVED'
        steps[2].save()
        self.assertEqual(self.profile.onboarding_progress_percentage, 75)
        self.assertFalse(self.profile.all_milestones_approved)

        # Approve 4 steps
        steps[3].status = 'APPROVED'
        steps[3].save()
        self.assertEqual(self.profile.onboarding_progress_percentage, 100)
        self.assertTrue(self.profile.all_milestones_approved)

    def test_toggle_roadmap_step_view(self):
        RoadmapStep.objects.filter(client=self.user).delete()
        create_default_roadmap_steps(self.user)
        step = RoadmapStep.objects.filter(client=self.user).first()
        self.assertEqual(step.status, 'DECLINED')

        # Toggle to APPROVED
        url = reverse('toggle_roadmap_step', kwargs={'step_id': step.id})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['new_status'], 'APPROVED')
        self.assertEqual(data['progress_percent'], 25)
        self.assertEqual(data['approved_count'], 1)
        self.assertEqual(data['total_count'], 4)

        # Refresh from db and verify profile sync
        step.refresh_from_db()
        self.assertEqual(step.status, 'APPROVED')
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.services_selected_status, 'APPROVED')

        # Toggle back to DECLINED
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['new_status'], 'DECLINED')
        self.assertEqual(data['progress_percent'], 0)

        step.refresh_from_db()
        self.assertEqual(step.status, 'DECLINED')
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.services_selected_status, 'DECLINED')


class BrandingAssetsTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_superuser(username='admin', password='adminpassword')
        self.client.login(username='admin', password='adminpassword')
        self.site_setting = SiteSetting.get_instance()

    def test_update_branding_assets_non_ajax(self):
        url = reverse('update_branding_assets')
        post_data = {
            'education_external_url': 'https://wisdom-tower.com'
        }
        response = self.client.post(url, post_data)
        self.assertRedirects(response, reverse('admin_panel'))
        
        # Verify db records
        self.site_setting.refresh_from_db()
        self.assertEqual(self.site_setting.education_external_url, 'https://wisdom-tower.com')
        
    def test_update_branding_assets_ajax(self):
        url = reverse('update_branding_assets')
        post_data = {
            'education_external_url': 'https://wisdom-tower.com/ajax'
        }
        response = self.client.post(url, post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')

        # Verify db records
        self.site_setting.refresh_from_db()
        self.assertEqual(self.site_setting.education_external_url, 'https://wisdom-tower.com/ajax')
