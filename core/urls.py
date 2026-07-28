from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('admin-messages/', views.message_dashboard, name='message_dash'),
    path('admin-reviews/', views.review_dash, name='review_dash'),
    path('settings/', views.profile_settings, name='profile_settings'),
    path('admin-panel/', views.admin_dashboard, name='admin_panel'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('delete-review/<int:review_id>/', views.delete_review, name='delete_review'),
    path('delete-project/<int:project_id>/', views.delete_project, name='delete_project'),
    path('delete-leader/<int:leader_id>/', views.delete_leader, name='delete_leader'),
    path('select-services/', views.select_services, name='select_services'),
    path('choose-pricing/', views.choose_pricing, name='choose_pricing'),
    path('client-dashboard/', views.client_dashboard, name='client_dashboard'),
    path('client-dashboard/<int:user_id>/', views.client_dashboard, name='client_dashboard_detail'),
    path('api/admin/clients/<int:client_id>/analytics/', views.ClientAnalyticsView.as_view(), name='client_analytics_api'),
    path('update-milestone/<int:milestone_id>/<str:new_status>/', views.update_milestone_status, name='update_milestone_status'),
    path('dashboard/admin/', views.milestone_admin_dashboard, name='milestone_admin_dashboard'),
    path('approve/<int:milestone_id>/', views.approve_milestone, name='approve_milestone'),
    path('admin-panel/roadmap/update/<int:step_id>/', views.update_roadmap_status, name='update_roadmap_status'),
    path('admin-panel/roadmap/step/<int:step_id>/update/', views.update_roadmap_step_status, name='update_roadmap_step_status'),
    path('client-dashboard/roadmap/step/<int:step_id>/toggle/', views.toggle_roadmap_step, name='toggle_roadmap_step'),
    path('api/clients/<int:client_id>/milestones-status/', views.client_milestone_status_api, name='client_milestone_status_api'),
    path('api/service-analytics/', views.service_analytics_api, name='service_analytics_api'),
    path('api/toggle-service/<int:service_id>/', views.toggle_service, name='toggle_service'),
    path('api/metric-entries/', views.metric_entries_api, name='metric_entries_api'),
    path('services/', views.services_page, name='services_page'),
    path('experience/', views.experience_page, name='experience_page'),
    path('api/active-services/', views.get_active_services, name='get_active_services'),
    path('api/team/add/', views.add_team_member_inline, name='add_team_member_inline'),
]


