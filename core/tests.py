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

        # Check that 4 steps exist and are PENDING
        steps = RoadmapStep.objects.filter(client=self.user).order_by('order')
        self.assertEqual(steps.count(), 4)
        for step in steps:
            self.assertEqual(step.status, 'PENDING')
        
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
        self.assertEqual(step.status, 'PENDING')

        # Make user staff since roadmap toggling is restricted to staff
        self.user.is_staff = True
        self.user.save()

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


from core.models import SubService, ServiceCategory

class WorkspaceAndAnalyticsTests(TestCase):
    def setUp(self):
        # Create staff user
        self.staff_user = User.objects.create_superuser(username='staffadmin', password='password123')
        # Create client users
        self.client_user = User.objects.create_user(username='client1', password='password123')
        self.other_client = User.objects.create_user(username='client2', password='password123')
        
        self.client_profile = ClientProfile.objects.get(user=self.client_user)
        self.other_profile = ClientProfile.objects.get(user=self.other_client)

        # Seed categories & services
        self.category = ServiceCategory.objects.create(title='Design', order=1)
        self.service = SubService.objects.create(
            service_category=self.category,
            category='DESIGN',
            title='Logo Design',
            short_explanation='Brand identity visual logo'
        )

    def test_client_can_retrieve_own_analytics(self):
        self.client.login(username='client1', password='password123')
        url = reverse('client_analytics_api', kwargs={'client_id': self.client_profile.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_client_cannot_retrieve_others_analytics(self):
        self.client.login(username='client1', password='password123')
        url = reverse('client_analytics_api', kwargs={'client_id': self.other_profile.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_staff_can_retrieve_any_client_analytics(self):
        self.client.login(username='staffadmin', password='password123')
        url = reverse('client_analytics_api', kwargs={'client_id': self.client_profile.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_staff_service_toggle_on_behalf_of_client(self):
        self.client.login(username='staffadmin', password='password123')
        url = reverse('toggle_service', kwargs={'service_id': self.service.id}) + f"?client_id={self.client_profile.user.id}"
        
        # Toggle service ON for client1
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['selected'])

        # Verify client1 has the service selected, but staff does not
        self.client_profile.refresh_from_db()
        self.assertTrue(self.client_profile.selected_services.filter(id=self.service.id).exists())
        
        staff_profile = ClientProfile.objects.get(user=self.staff_user)
        self.assertFalse(staff_profile.selected_services.filter(id=self.service.id).exists())


from core.models import Notification

class NotificationSystemTests(TestCase):
    def setUp(self):
        self.admin1 = User.objects.create_superuser(username='notif_admin1', password='password123')
        self.admin2 = User.objects.create_superuser(username='notif_admin2', password='password123')
        self.client_user = User.objects.create_user(username='notif_client', password='password123')
        
        # Complete onboarding to avoid redirects in views
        profile = ClientProfile.objects.get(user=self.client_user)
        profile.onboarding_completed = True
        profile.save()
        
        # Clear setup-induced notifications
        Notification.objects.all().delete()
        
        # Service details for metrics
        self.category = ServiceCategory.objects.create(title='Content', order=2)
        self.subservice = SubService.objects.create(
            service_category=self.category,
            category='CONTENT',
            title='Blog Post Writing',
            short_explanation='Write SEO optimized blogs'
        )

    def test_new_client_signup_notification(self):
        # Create a new non-staff user to trigger signup notification
        new_client = User.objects.create_user(username='new_signup_user', password='password123')
        
        # Verify notification created for each admin
        admin1_notifs = Notification.objects.filter(recipient=self.admin1, notification_type='client_signup')
        admin2_notifs = Notification.objects.filter(recipient=self.admin2, notification_type='client_signup')
        self.assertEqual(admin1_notifs.count(), 1)
        self.assertEqual(admin2_notifs.count(), 1)
        self.assertIn("new_signup_user", admin1_notifs.first().message)

    def test_contact_message_notification(self):
        self.client.login(username='notif_client', password='password123')
        contact_url = reverse('contact')
        response = self.client.post(contact_url, {
            'subject': 'Help Request',
            'message_body': 'I need help with my account.'
        })
        self.assertEqual(response.status_code, 302) # Redirects to home
        
        # Verify admin notifications
        admin_notifs = Notification.objects.filter(recipient=self.admin1, notification_type='contact_message')
        self.assertEqual(admin_notifs.count(), 1)
        self.assertEqual(admin_notifs.first().title, "New Contact Message")

    def test_review_submission_notification(self):
        self.client.login(username='notif_client', password='password123')
        # Review is submitted via home view POST
        home_url = reverse('home')
        response = self.client.post(home_url, {
            'rating': '5',
            'comment': 'Awesome services!'
        })
        self.assertEqual(response.status_code, 302) # Redirects to home
        
        # Verify admin notifications
        admin_notifs = Notification.objects.filter(recipient=self.admin1, notification_type='new_review')
        self.assertEqual(admin_notifs.count(), 1)
        self.assertIn("5-star", admin_notifs.first().message)

    def test_metric_update_client_notification(self):
        # Login as admin to update metric entries
        self.client.login(username='notif_admin1', password='password123')
        url = reverse('metric_entries_api')
        response = self.client.post(url, {
            'client_username': 'notif_client',
            'sub_service_id': self.subservice.id,
            'value': '10.5',
            'date': '2026-07-30',
            'note': 'Good progress'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Verify client notification
        client_notifs = Notification.objects.filter(recipient=self.client_user, notification_type='metric_update')
        self.assertEqual(client_notifs.count(), 1)
        self.assertEqual(client_notifs.first().title, "Analytics Metric Updated")
        
        # Staff user should NOT get this notification
        admin_notifs = Notification.objects.filter(recipient=self.admin1, notification_type='metric_update')
        self.assertEqual(admin_notifs.count(), 0)

    def test_mark_notification_as_read(self):
        # Create a notification first
        notif = Notification.objects.create(
            recipient=self.client_user,
            title="Test Notification",
            message="Sample message",
            notification_type="metric_update"
        )
        self.assertFalse(notif.is_read)

        # Login as client to mark read
        self.client.login(username='notif_client', password='password123')
        url = reverse('mark_notification_read', kwargs={'notification_id': notif.id})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['unread_notifications_count'], 0)
        
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)
