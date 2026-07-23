from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from allauth.account.forms import ChangePasswordForm
from allauth.account.views import PasswordChangeView
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.functions import TruncDate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from .models import Review, ContactMessage, Service, Project, SiteSetting, TeamMember, ServiceItem, ClientProfile, ClientActivityLog
from .serializers import ClientAnalyticsSerializer
from .forms import SiteSettingForm

def home(request):
    team_members = TeamMember.objects.all().order_by('order')
    if not request.user.is_authenticated:
        return render(request, 'core/landing.html', {'team_members': team_members})
    
    # Force onboarding flow for regular clients
    if not request.user.is_staff:
        profile, created = ClientProfile.objects.get_or_create(user=request.user)
        if not profile.onboarding_completed:
            return redirect('select_services')
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        if rating and comment:
            Review.objects.create(
                user=request.user,
                rating=int(rating),
                comment=comment
            )
            messages.success(request, "Thank you for your review!")
            return redirect('home')

    reviews = Review.objects.all().select_related('user').order_by('-created_at')
    services = Service.objects.all().order_by('order')
    projects = Project.objects.all().order_by('-created_at')
    site_setting = SiteSetting.objects.first()
    return render(request, 'core/dashboard.html', {
        'reviews': reviews,
        'services': services,
        'projects': projects,
        'site_setting': site_setting,
        'team_members': team_members,
    })


def staff_check(user):
    return user.is_staff

@staff_member_required
def message_dashboard(request):
    messages_list = ContactMessage.objects.all().select_related('user')
    return render(request, 'core/message_dash.html', {'messages_list': messages_list})

@user_passes_test(staff_check)
def review_dash(request):
    reviews_list = Review.objects.all().select_related('user')
    return render(request, 'core/review_dash.html', {'reviews_list': reviews_list})

@login_required
def contact(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message_content = request.POST.get('message_body')
        if subject and message_content:
            ContactMessage.objects.create(
                user=request.user,
                subject=subject,
                message=message_content
            )
            messages.success(request, "Message sent successfully!")
            return redirect('home')
    return render(request, 'core/contact.html')

@login_required
def profile_settings(request):
    password_form = ChangePasswordForm(user=request.user)
    if request.method == 'POST' and 'change_password' in request.POST:
        password_form = ChangePasswordForm(user=request.user, data=request.POST)
        if password_form.is_valid():
            password_form.save()
            messages.success(request, "Password changed successfully!")
            return redirect('profile_settings')
        else:
            messages.error(request, "Please correct the error below.")

    return render(request, 'account/settings.html', {
        'password_form': password_form,
    })

@staff_member_required
def admin_dashboard(request):
    users = User.objects.all().order_by('-date_joined')
    reviews = Review.objects.all().select_related('user').order_by('-created_at')
    projects = Project.objects.all().order_by('-created_at')
    team_members = TeamMember.objects.order_by('order')
    site_setting = SiteSetting.objects.first()
    client_profiles = ClientProfile.objects.select_related('user').prefetch_related('selected_services').all().order_by('-user__date_joined')
    
    if not site_setting:
        site_setting = SiteSetting.objects.create()

    if request.method == 'POST' and 'update_site_settings' in request.POST:
        if 'delete_video' in request.POST:
            if site_setting.our_story_video:
                site_setting.our_story_video.delete(save=False)
                site_setting.our_story_video = None
                site_setting.save()
            messages.success(request, "Our Story video removed successfully.")
            return redirect('admin_dashboard')

        if 'delete_image' in request.POST:
            if site_setting.our_story_image:
                site_setting.our_story_image.delete(save=False)
                site_setting.our_story_image = None
                site_setting.save()
            messages.success(request, "Fallback image removed successfully.")
            return redirect('admin_dashboard')

        form = SiteSettingForm(request.POST, request.FILES, instance=site_setting)
        if form.is_valid():
            form.save()
            messages.success(request, "Platform branding and media settings updated successfully!")
            return redirect('admin_dashboard')

    else:
        form = SiteSettingForm(instance=site_setting)

    return render(request, 'core/admin_dashboard.html', {
        'users': users,
        'reviews': reviews,
        'projects': projects,
        'team_members': team_members,
        'site_setting': site_setting,
        'site_form': form,
        'client_profiles': client_profiles,
    })

@staff_member_required
def delete_review(request, review_id):
    review = Review.objects.get(id=review_id)
    review.delete()
    messages.success(request, "Review deleted successfully.")
    return redirect('admin_dashboard')

@staff_member_required
def delete_project(request, project_id):
    project = Project.objects.get(id=project_id)
    project.delete()
    messages.success(request, "Project deleted successfully.")
    return redirect('admin_dashboard')

@staff_member_required
def delete_leader(request, leader_id):
    leader = TeamMember.objects.get(id=leader_id)
    leader.delete()
    messages.success(request, "Team member deleted successfully.")
    return redirect('admin_dashboard')


@login_required
def select_services(request):
    profile, created = ClientProfile.objects.get_or_create(user=request.user)
    if profile.onboarding_completed:
        return redirect('home')
        
    if request.method == 'POST':
        selected_ids = request.POST.getlist('services')
        profile.selected_services.set(selected_ids)
        profile.save()
        return redirect('choose_pricing')
        
    services = ServiceItem.objects.all()
    categories_dict = {}
    for choice_key, choice_name in ServiceItem.CATEGORY_CHOICES:
        categories_dict[choice_key] = {
            'name': choice_name,
            'items': services.filter(category=choice_key)
        }
        
    selected_service_ids = list(profile.selected_services.values_list('id', flat=True))
    
    return render(request, 'core/select_services.html', {
        'categories': categories_dict,
        'selected_service_ids': selected_service_ids,
    })


@login_required
def choose_pricing(request):
    profile, created = ClientProfile.objects.get_or_create(user=request.user)
    if profile.onboarding_completed:
        return redirect('home')
        
    if request.method == 'POST':
        tier = request.POST.get('tier')
        if tier:
            profile.chosen_tier = tier
            profile.onboarding_completed = True
            profile.save()
            messages.success(request, "Setup completed successfully! Welcome to Nexo.")
            return redirect('home')
            
    return render(request, 'core/choose_pricing.html', {
        'profile': profile,
    })


@login_required
def client_dashboard(request, user_id=None):
    if user_id is not None:
        if not request.user.is_staff and request.user.id != user_id:
            messages.error(request, "You are not authorized to view this dashboard.")
            return redirect('client_dashboard')
        target_user = User.objects.get(id=user_id)
    else:
        target_user = request.user
        
    profile, created = ClientProfile.objects.get_or_create(user=target_user)
    selected_services = profile.selected_services.all()

    # Group selected services by category for organized display
    categories_map = dict(ServiceItem.CATEGORY_CHOICES)
    grouped_services = {}
    for svc in selected_services:
        cat_display = categories_map.get(svc.category, svc.category)
        if cat_display not in grouped_services:
            grouped_services[cat_display] = []
        grouped_services[cat_display].append(svc)

    # For standard users, treat anything that isn't 'APPROVED' as invisible (empty)
    if not request.user.is_staff:
        if profile.services_selected_status != 'APPROVED':
            profile.services_selected_status = ''
        if profile.team_assignment_status != 'APPROVED':
            profile.team_assignment_status = ''
        if profile.kickoff_call_status != 'APPROVED':
            profile.kickoff_call_status = ''
        if profile.deliverables_begin_status != 'APPROVED':
            profile.deliverables_begin_status = ''

    return render(request, 'core/client_dashboard.html', {
        'profile': profile,
        'dashboard_user': target_user,
        'selected_services': selected_services,
        'grouped_services': grouped_services,
        'onboarding_step': profile.onboarding_step,
        'project_lead_assigned': profile.project_lead_assigned or (profile.assigned_lead is not None),
    })


class ClientAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, client_id, *args, **kwargs):
        profile = get_object_or_404(ClientProfile, id=client_id)
        
        # 1. Fetch engagement data (aggregate activity log by date)
        engagement = (
            ClientActivityLog.objects.filter(client=profile)
            .annotate(date=TruncDate('timestamp'))
            .values('date')
            .annotate(score=Count('id'))
            .order_by('date')
        )
        
        engagement_list = [
            {
                'date': entry['date'],
                'score': entry['score']
            }
            for entry in engagement if entry['date'] is not None
        ]
        
        # 2. Fetch service data (active service count mapping)
        active_services = (
            profile.selected_services.values('category')
            .annotate(count=Count('id'))
        )
        active_counts = {entry['category']: entry['count'] for entry in active_services}
        
        # Map active services against all 10 categories
        category_choices = getattr(ServiceItem, 'CATEGORY_CHOICES', [])
        service_list = [
            {
                'category': category_name,
                'count': active_counts.get(category_key, 0)
            }
            for category_key, category_name in category_choices
        ]
        
        # 3. Payload Construction
        project_lead_assigned = (profile.assigned_lead is not None) or profile.project_lead_assigned
        current_step = profile.onboarding_step
            
        reg_date = getattr(profile, 'registration_date', None) or profile.user.date_joined
        payload = {
            'client_name': profile.user.get_full_name() or profile.user.username,
            'registration_date': reg_date,
            'project_lead_assigned': project_lead_assigned,
            'current_step': current_step,
            'services_selected_status': profile.services_selected_status,
            'team_assignment_status': profile.team_assignment_status,
            'kickoff_call_status': profile.kickoff_call_status,
            'deliverables_begin_status': profile.deliverables_begin_status,
            'progress_percentage': profile.onboarding_progress_percentage,
            'engagement_data': engagement_list,
            'service_data': service_list,
        }
        
        serializer = ClientAnalyticsSerializer(payload)
        return Response(serializer.data)


from django.http import HttpResponseForbidden, JsonResponse

def update_milestone_status(request, milestone_id, new_status):
    # Strictly enforces that only users with request.user.is_staff set to True can execute this change
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseForbidden("Forbidden: Only staff members can update milestone statuses.")
    
    # Load the ClientProfile model instance
    profile = get_object_or_404(ClientProfile, id=milestone_id)
    
    # Support overriding step/milestone selection via type query param
    milestone_type = request.GET.get('type')
    
    if milestone_type == 'services':
        profile.services_selected_status = new_status
    elif milestone_type == 'team':
        profile.team_assignment_status = new_status
    elif milestone_type == 'kickoff':
        profile.kickoff_call_status = new_status
    elif milestone_type == 'deliverables':
        profile.deliverables_begin_status = new_status
    else:
        # Fallback to the current onboarding step if no type parameter is passed
        if profile.onboarding_step == 1:
            profile.services_selected_status = new_status
        elif profile.onboarding_step == 2:
            profile.team_assignment_status = new_status
        elif profile.onboarding_step == 3:
            profile.kickoff_call_status = new_status
        elif profile.onboarding_step == 4:
            profile.deliverables_begin_status = new_status

    profile.save()
    
    return JsonResponse({
        'status': 'success',
        'message': f"Milestone status updated to {new_status}.",
        'progress': profile.onboarding_progress_percentage
    })


@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
def milestone_admin_dashboard(request):
    if request.method == 'POST':
        profile_id = request.POST.get('profile_id')
        milestone_field = request.POST.get('milestone_field')
        if profile_id and milestone_field:
            profile = get_object_or_404(ClientProfile, id=profile_id)
            if milestone_field == 'services':
                profile.services_selected_status = 'APPROVED'
            elif milestone_field == 'team':
                profile.team_assignment_status = 'APPROVED'
            elif milestone_field == 'kickoff':
                profile.kickoff_call_status = 'APPROVED'
            elif milestone_field == 'deliverables':
                profile.deliverables_begin_status = 'APPROVED'
            profile.save()
            messages.success(request, f"Milestone for {profile.user.username} approved successfully!")
        return redirect('milestone_admin_dashboard')

    profiles = ClientProfile.objects.all().select_related('user').order_by('-user__date_joined')
    return render(request, 'admin_dashboard.html', {
        'profiles': profiles
    })


@user_passes_test(lambda u: u.is_superuser)
def approve_milestone(request, milestone_id):
    profile = get_object_or_404(ClientProfile, id=milestone_id)
    milestone_type = request.GET.get('type')
    
    if milestone_type == 'services':
        profile.services_selected_status = 'APPROVED'
    elif milestone_type == 'team':
        profile.team_assignment_status = 'APPROVED'
    elif milestone_type == 'kickoff':
        profile.kickoff_call_status = 'APPROVED'
    elif milestone_type == 'deliverables':
        profile.deliverables_begin_status = 'APPROVED'
    else:
        # Default fallback: update current onboarding step
        if profile.onboarding_step == 1:
            profile.services_selected_status = 'APPROVED'
        elif profile.onboarding_step == 2:
            profile.team_assignment_status = 'APPROVED'
        elif profile.onboarding_step == 3:
            profile.kickoff_call_status = 'APPROVED'
        elif profile.onboarding_step == 4:
            profile.deliverables_begin_status = 'APPROVED'
            
    profile.save()
    messages.success(request, "Milestone status updated to APPROVED.")
    
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('client_dashboard_detail', user_id=profile.user.id)


def client_milestone_status_api(request, client_id):
    from django.db.models import Count
    from .models import ServiceItem
    profile = get_object_or_404(ClientProfile, id=client_id)
    milestones = [
        {
            'id': m['id'],
            'name': m['name'],
            'status': m['status'],
            'step_number': m['step_number']
        }
        for m in profile.milestones_list
    ]
    
    # Calculate service utilization/allocations
    active_services = (
        profile.selected_services.values('category')
        .annotate(count=Count('id'))
    )
    active_counts = {entry['category']: entry['count'] for entry in active_services}
    category_choices = getattr(ServiceItem, 'CATEGORY_CHOICES', [])
    
    services_progress = [
        {
            'category': category_name,
            'count': active_counts.get(category_key, 0),
            'progress': 100 if profile.deliverables_begin_status == 'APPROVED' else (profile.onboarding_progress_percentage)
        }
        for category_key, category_name in category_choices
        if active_counts.get(category_key, 0) > 0
    ]

    return JsonResponse({
        'client_id': profile.id,
        'client_name': profile.user.username,
        'progress_percentage': profile.onboarding_progress_percentage,
        'milestones': milestones,
        'services_progress': services_progress
    })



from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def service_analytics_api(request):
    from .models import ServiceAnalytics
    from django.contrib.auth.models import User
    from datetime import datetime
    import json

    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        else:
            data = request.POST

        client_username = data.get('client_username')
        service_name = data.get('service_name')
        metric_name = data.get('metric_name', 'Value')
        metric_value = data.get('metric_value')
        explanation = data.get('explanation', '')
        date_str = data.get('date')

        if not client_username or not service_name or metric_value is None:
            return JsonResponse({'status': 'error', 'message': 'Missing required fields: client_username, service_name, and metric_value.'}, status=400)

        try:
            client = User.objects.get(username=client_username)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': f'Client with username "{client_username}" does not exist.'}, status=404)

        try:
            date_val = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

        record = ServiceAnalytics.objects.create(
            client=client,
            service_name=service_name,
            metric_name=metric_name,
            metric_value=float(metric_value),
            explanation=explanation,
            date=date_val
        )
        return JsonResponse({
            'status': 'success',
            'record': {
                'id': record.id,
                'client': record.client.username,
                'service_name': record.service_name,
                'metric_name': record.metric_name,
                'metric_value': record.metric_value,
                'explanation': record.explanation,
                'date': record.date.strftime('%Y-%m-%d')
            }
        })

    # GET request: Optimized with select_related, only, date delta, and O(1) Hash Map structure
    service_name = request.GET.get('service_name')
    client_username = request.GET.get('client_username')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    since = request.GET.get('since')

    queryset = (
        ServiceAnalytics.objects.all()
        .select_related('client')
        .only('id', 'client__username', 'service_name', 'metric_name', 'metric_value', 'date', 'explanation')
    )

    if service_name:
        queryset = queryset.filter(service_name=service_name)
    if client_username:
        queryset = queryset.filter(client__username=client_username)
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    if since:
        queryset = queryset.filter(date__gte=since)

    if not queryset.exists():
        return JsonResponse({
            "status": "no_change",
            "message": "No changes recorded for this period."
        })

    # Group into an O(1) constant-time Hash Map grouped by service name
    grouped_data = {}
    for record in queryset:
        s_name = record.service_name
        if s_name not in grouped_data:
            grouped_data[s_name] = {
                'metric_name': record.metric_name,
                'points': []
            }
        grouped_data[s_name]['points'].append({
            'id': record.id,
            'client': record.client.username,
            'metric_value': record.metric_value,
            'explanation': record.explanation,
            'date': record.date.strftime('%Y-%m-%d')
        })

    return JsonResponse({
        'status': 'success',
        'data': grouped_data
    })


# ─────────────────────────────────────────────────────────────────────────────
# MetricEntry API — aggregation-based analytics endpoint
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
def metric_entries_api(request):
    """
    GET  /api/metric-entries/?client_username=X[&service_name=Y][&period=week|month|year]
         Returns per-service aggregated totals (week / month / year) PLUS
         the ordered daily points for sparkline rendering.

    POST /api/metric-entries/
         Body (JSON): { client_username, service_name, value, date, note }
         Creates or updates the MetricEntry for that client+service+date.
         Superuser / staff only.
    """
    from .models import MetricEntry
    from django.db.models import Sum
    from django.db.models.functions import TruncWeek, TruncMonth, TruncYear
    from django.contrib.auth.models import User
    from datetime import datetime, date as date_type
    import json

    # ── POST: Admin creates / upserts a daily entry ──────────────────────────
    if request.method == 'POST':
        if not (request.user.is_authenticated and request.user.is_staff):
            return JsonResponse({'status': 'error', 'message': 'Forbidden.'}, status=403)

        try:
            data = json.loads(request.body)
        except (ValueError, TypeError):
            data = request.POST.dict()

        client_username = data.get('client_username', '').strip()
        service_name    = data.get('service_name', '').strip()
        value_raw       = data.get('value')
        date_str        = data.get('date', '').strip()
        note            = data.get('note', '').strip()

        if not client_username or not service_name or value_raw is None:
            return JsonResponse(
                {'status': 'error', 'message': 'client_username, service_name, and value are required.'},
                status=400
            )

        try:
            client = User.objects.get(username=client_username)
        except User.DoesNotExist:
            return JsonResponse(
                {'status': 'error', 'message': f'No user with username "{client_username}".'},
                status=404
            )

        try:
            value = float(value_raw)
        except (ValueError, TypeError):
            return JsonResponse({'status': 'error', 'message': 'value must be a number.'}, status=400)

        try:
            entry_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date_type.today()
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'date must be YYYY-MM-DD.'}, status=400)

        entry, created = MetricEntry.objects.update_or_create(
            client=client,
            service_name=service_name,
            date=entry_date,
            defaults={'value': value, 'note': note}
        )

        return JsonResponse({
            'status': 'created' if created else 'updated',
            'entry': {
                'id':           entry.id,
                'client':       client.username,
                'service_name': entry.service_name,
                'value':        entry.value,
                'date':         entry.date.strftime('%Y-%m-%d'),
                'note':         entry.note,
                'last_updated': entry.last_updated.isoformat() if entry.last_updated else None
            }
        })

    # ── GET: Return aggregated data per service ───────────────────────────────
    client_username = request.GET.get('client_username', '').strip()
    service_name    = request.GET.get('service_name', '').strip()
    date_query      = request.GET.get('date', '').strip()
    start_date      = request.GET.get('start_date', '').strip()
    end_date        = request.GET.get('end_date', '').strip()

    if not client_username:
        return JsonResponse({'status': 'error', 'message': 'client_username is required.'}, status=400)

    # 1. State-aware single date value query for form pre-populating
    if service_name and date_query:
        try:
            entry = MetricEntry.objects.get(
                client__username=client_username,
                service_name=service_name,
                date=date_query
            )
            return JsonResponse({
                'status': 'success',
                'value': entry.value,
                'note': entry.note,
                'last_updated': entry.last_updated.isoformat() if entry.last_updated else None
            })
        except MetricEntry.DoesNotExist:
            return JsonResponse({
                'status': 'success',
                'value': 0.0,
                'note': '',
                'last_updated': None
            })

    # 2. General aggregated service metric query
    qs = MetricEntry.objects.filter(client__username=client_username).order_by('date')

    if service_name:
        qs = qs.filter(service_name=service_name)
    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)

    if not qs.exists():
        return JsonResponse({
            'status': 'no_data',
            'message': 'No metric entries found for this client.',
            'data': {}
        })

    # Build per-service aggregations in a single pass through the queryset,
    # keeping an ordered list of daily points for chart rendering.
    today = date_type.today()

    # Pre-compute period boundaries once
    from datetime import timedelta
    week_start  = today - timedelta(days=today.weekday())
    week_end    = week_start + timedelta(days=6)
    month_start = today.replace(day=1)
    year_start  = today.replace(month=1, day=1)

    service_map = {}   # { service_name: { week_total, month_total, year_total, daily_points, last_updated } }

    for entry in qs:
        svc = entry.service_name
        if svc not in service_map:
            service_map[svc] = {
                'week_total':  0.0,
                'month_total': 0.0,
                'year_total':  0.0,
                'daily_points': [],
                'last_updated': None,
            }
        rec = service_map[svc]

        # Accumulate period totals
        if week_start <= entry.date <= week_end:
            rec['week_total']  = round(rec['week_total']  + entry.value, 4)
        if entry.date.year == today.year and entry.date.month == today.month:
            rec['month_total'] = round(rec['month_total'] + entry.value, 4)
        if entry.date.year == today.year:
            rec['year_total']  = round(rec['year_total']  + entry.value, 4)

        if not rec['last_updated'] or entry.last_updated.isoformat() > rec['last_updated']:
            rec['last_updated'] = entry.last_updated.isoformat()

        rec['daily_points'].append({
            'id':    entry.id,
            'date':  entry.date.strftime('%Y-%m-%d'),
            'value': entry.value,
            'note':  entry.note,
        })

    return JsonResponse({
        'status': 'success',
        'data':   service_map,
    })


def get_active_services(request):
    """
    Returns a list of unique service categories that are currently approved
    for the client. Filters by the milestone status (services_selected_status == 'APPROVED').
    """
    from django.contrib.auth.models import User
    from django.db.models import Count
    from .models import ClientProfile, ServiceItem

    username = request.GET.get('client_username', '').strip()
    if username:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found.'}, status=404)
    else:
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Unauthorized.'}, status=401)
        user = request.user

    try:
        profile = user.nexo_profile
    except AttributeError:
        return JsonResponse({'status': 'success', 'services': []})

    # Only return selected services if selection is APPROVED/active
    if profile.services_selected_status == 'APPROVED':
        active_cats = (
            profile.selected_services.values('category')
            .annotate(count=Count('id'))
        )
        categories_map = dict(ServiceItem.CATEGORY_CHOICES)
        services_list = []
        for entry in active_cats:
            cat_key = entry['category']
            cat_display = categories_map.get(cat_key, cat_key)
            services_list.append({
                'category': cat_display,
                'count': entry['count']
            })
        return JsonResponse({'status': 'success', 'services': services_list})
    else:
        return JsonResponse({'status': 'success', 'services': []})


@csrf_exempt
def add_team_member_inline(request):
    """
    Staff-only endpoint to create or update a TeamMember (leader) via AJAX/JSON without leaving the page.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse({'status': 'error', 'message': 'Forbidden: Staff access required.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed.'}, status=405)

    import json
    try:
        data = json.loads(request.body)
    except (ValueError, TypeError):
        data = request.POST

    member_id = data.get('id')
    name = data.get('name', '').strip()
    job_role = data.get('job_role', '').strip()
    bio = data.get('bio', '').strip()
    image_url = data.get('image_url', '').strip()
    order_val = data.get('order', 0)

    if not name or not job_role:
        return JsonResponse({'status': 'error', 'message': 'Name and job role are required.'}, status=400)

    try:
        order = int(order_val)
    except (ValueError, TypeError):
        order = 0

    if member_id:
        try:
            member = TeamMember.objects.get(id=member_id)
            member.name = name
            member.job_role = job_role
            member.bio = bio
            if image_url:
                member.image_url = image_url
            member.order = order
            member.save()
            action = 'updated'
        except TeamMember.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Leader not found.'}, status=404)
    else:
        member = TeamMember.objects.create(
            name=name,
            job_role=job_role,
            bio=bio,
            image_url=image_url,
            order=order
        )
        action = 'created'

    return JsonResponse({
        'status': 'success',
        'action': action,
        'member': {
            'id': member.id,
            'name': member.name,
            'job_role': member.job_role,
            'bio': member.bio or '',
            'image_display': member.image_display or '',
            'order': member.order
        }
    })



def services_page(request):
    """
    Public/Unified Services Catalog page accessible to both unauthenticated visitors and logged-in clients.
    """
    return render(request, 'core/services.html')


def experience_page(request):
    """
    Experience page rendering Experience items grouped specifically under Video Experience and Web Experience.
    All additions/modifications occur via Django Admin.
    """
    from .models import ExperienceCategory, Experience
    categories = ExperienceCategory.objects.prefetch_related('experiences').all()
    
    video_category = ExperienceCategory.objects.filter(name__icontains='Video').first()
    web_category = ExperienceCategory.objects.filter(name__icontains='Web').first()
    
    video_experiences = video_category.experiences.all() if video_category else Experience.objects.none()
    web_experiences = web_category.experiences.all() if web_category else Experience.objects.none()

    return render(request, 'core/experience.html', {
        'categories': categories,
        'video_category': video_category,
        'web_category': web_category,
        'video_experiences': video_experiences,
        'web_experiences': web_experiences,
    })



