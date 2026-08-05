from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from allauth.account.forms import ChangePasswordForm
from allauth.account.views import PasswordChangeView
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from .models import Review, ContactMessage, Service, Project, SiteSetting, TeamMember, ServiceItem, ClientProfile, ClientActivityLog, ProjectCategory, PhoneNumber, ServiceCategory, RoadmapStep, Experience, ExperienceCategory
from .serializers import ClientAnalyticsSerializer
from .forms import SiteSettingForm, ProjectForm

def home(request):
    team_members = TeamMember.objects.all().order_by('order')
    categories = ServiceCategory.objects.all().prefetch_related('subservices').order_by('order')
    services = Service.objects.all().order_by('order')
    experiences = Experience.objects.select_related('category').all().order_by('-created_at')
    experience_categories = ExperienceCategory.objects.all().order_by('order')
    fallback_categories = []
    selected_service_ids = []

    if request.user.is_authenticated:
        profile, _ = ClientProfile.objects.get_or_create(user=request.user)
        selected_service_ids = list(profile.selected_services.values_list('id', flat=True))

        if not request.user.is_staff and not profile.onboarding_completed:
            return redirect('select_services')

    if request.method == 'POST' and request.user.is_authenticated:
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        if rating and comment:
            Review.objects.create(
                user=request.user,
                rating=int(rating),
                comment=comment
            )
            try:
                from .models import create_notification
                admins = User.objects.filter(is_staff=True)
                create_notification(
                    recipients=admins,
                    title="New Client Review",
                    message=f"New {rating}-star review submitted by {request.user.username}.",
                    notification_type="new_review"
                )
            except Exception:
                pass
            messages.success(request, "Thank you for your review!")
            return redirect('home')

    reviews = Review.objects.all().select_related('user').order_by('-created_at')
    projects = Project.objects.all().order_by('-created_at')
    site_setting = SiteSetting.objects.first()

    ProjectCategory.ensure_standard_categories()
    standard_slugs = [slug for slug, _, _ in ProjectCategory.STANDARD_CATEGORIES]
    project_categories = ProjectCategory.objects.filter(slug__in=standard_slugs).order_by('order')
    project_groups = []
    for category in project_categories:
        group_projects = category.projects.all().order_by('-created_at')
        if category.slug == 'video-experience':
            for project in group_projects:
                project.is_playable = bool(project.video)
        project_groups.append({
            'category': category,
            'projects': group_projects,
        })

    if not categories.exists():
        fallback_categories = [
            {
                'title': 'Graphic & Print Design',
                'icon_class': 'fas fa-palette',
                'description': 'Visual identity crafted for print and digital impact.',
                'subservices': [
                    'Visual communication & brand identity',
                    'Presentation slide design (PowerPoint, Google Slides, Canva)',
                    'Book covers & eBook design',
                    'Resume/CV design',
                    'Posters, flyers, brochures & leaflets',
                    'Business cards, stickers & digital artwork',
                ],
            },
            {
                'title': 'Writing & Editorial',
                'icon_class': 'fas fa-pen-nib',
                'description': 'Words that persuade, inform, and convert.',
                'subservices': [
                    'Article and blog writing',
                    'Website content writing',
                    'Copywriting (ads, product descriptions)',
                    'Scriptwriting (YouTube, podcasts, short films)',
                    'Speech writing & creative fiction stories',
                    'Technical writing, proposal & grant writing',
                    'Editing, proofreading, rewriting & paraphrasing',
                ],
            },
            {
                'title': 'Academic & Research Support',
                'icon_class': 'fas fa-graduation-cap',
                'description': 'Rigorous research and academic formatting.',
                'subservices': [
                    'Thesis & dissertation writing support',
                    'Academic editing & formatting (APA, MLA, Chicago, Vancouver)',
                    'Research summaries, proposals & abstracts',
                    'Referencing & citation management',
                    'Plagiarism checking & reduction',
                    'PowerPoint presentations for research defense',
                ],
            },
            {
                'title': 'Data & Tech Solutions',
                'icon_class': 'fas fa-database',
                'description': 'Custom web software, APIs, and analytics engineering.',
                'subservices': [
                    'Custom website & web app development',
                    'E-commerce & business system development',
                    'API integration & backend systems',
                    'Data analysis & business intelligence dashboards',
                    'Automation & workflow scripting',
                    'Digital tools & SaaS product consulting',
                ],
            },
            {
                'title': 'Web & Digital Marketing',
                'icon_class': 'fas fa-bullhorn',
                'description': 'Strategies that grow traffic, leads, and conversions.',
                'subservices': [
                    'SEO strategy & implementation',
                    'Social media management & content calendars',
                    'Paid advertising (Google Ads, Meta Ads)',
                    'Email marketing campaigns',
                    'Content strategy & editorial planning',
                    'Influencer and affiliate marketing coordination',
                ],
            },
            {
                'title': 'Business Strategy & Admin',
                'icon_class': 'fas fa-briefcase',
                'description': 'Professional frameworks to grow and manage your enterprise.',
                'subservices': [
                    'Business plan writing',
                    'Market research & competitor analysis',
                    'Financial modeling & projections',
                    'Virtual assistant services',
                    'HR & recruitment consulting',
                    'Startup advisory & pitch deck creation',
                ],
            },
            {
                'title': 'Education & Multimedia',
                'icon_class': 'fas fa-chalkboard-teacher',
                'description': 'Interactive e-learning content and instructional media.',
                'subservices': [
                    'E-learning course creation',
                    'Instructional video production & editing',
                    'Motion graphics & animated explainers',
                    'Training materials & workshop content',
                    'Podcast editing & audio production',
                    'YouTube channel management & content strategy',
                ],
            },
        ]

    context = {
        'reviews': reviews,
        'services': services,
        'experiences': experiences,
        'experience_categories': experience_categories,
        'projects': projects,
        'site_setting': site_setting,
        'team_members': team_members,
        'categories': categories,
        'fallback_categories': fallback_categories,
        'selected_service_ids': selected_service_ids,
        'project_categories': project_categories,
        'project_groups': project_groups,
        'site_settings': site_setting,
    }

    if request.user.is_authenticated and request.user.is_staff:
        return render(request, 'core/dashboard.html', context)

    return render(request, 'core/landing.html', context)


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
            try:
                from .models import create_notification
                admins = User.objects.filter(is_staff=True)
                create_notification(
                    recipients=admins,
                    title="New Contact Message",
                    message=f"New message from {request.user.username}: '{subject}'",
                    notification_type="contact_message"
                )
            except Exception:
                pass
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

    notifications = request.user.notifications.all()

    return render(request, 'account/settings.html', {
        'password_form': password_form,
        'notifications': notifications,
    })


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    from .models import Notification
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({
        'status': 'success',
        'unread_notifications_count': unread_count,
        'notification_id': notification.id
    })

@staff_member_required
def admin_dashboard(request):
    ProjectCategory.ensure_standard_categories()
    users = User.objects.all().order_by('-date_joined')
    reviews = Review.objects.all().select_related('user').order_by('-created_at')
    projects = Project.objects.select_related('category_fk').all().order_by('-created_at')
    team_members = TeamMember.objects.order_by('order')
    site_setting = SiteSetting.objects.first()
    client_profiles = ClientProfile.objects.select_related('user').prefetch_related('selected_services').all().order_by('-user__date_joined')
    
    if not site_setting:
        site_setting = SiteSetting.objects.create()

    project_form = ProjectForm()
    form = SiteSettingForm(instance=site_setting)
    if request.method == 'POST':
        if 'add_project' in request.POST:
            project_form = ProjectForm(request.POST, request.FILES)
            if project_form.is_valid():
                project_form.save()
                messages.success(request, "New project added to the portfolio successfully!")
                return redirect('admin_panel')

    # Convert queryset to list and attach roadmap steps to each profile to avoid DB hits in template
    client_profiles = list(client_profiles)
    for profile in client_profiles:
        profile.roadmap_steps_qs = RoadmapStep.objects.filter(client=profile.user).order_by('order')

    return render(request, 'core/admin_dashboard.html', {
        'users': users,
        'reviews': reviews,
        'projects': projects,
        'team_members': team_members,
        'site_setting': site_setting,
        'site_form': form,
        'project_form': project_form,
        'client_profiles': client_profiles,
    })


@staff_member_required
def update_branding_assets(request):
    site_setting = SiteSetting.get_instance()
    
    if request.method == 'POST':
        if 'delete_video' in request.POST:
            if site_setting.our_story_video:
                site_setting.our_story_video.delete(save=False)
                site_setting.our_story_video = None
                site_setting.save()
            messages.success(request, "Our Story video removed successfully.")
            return redirect('admin_panel')

        if 'delete_image' in request.POST:
            if site_setting.our_story_image:
                site_setting.our_story_image.delete(save=False)
                site_setting.our_story_image = None
                site_setting.save()
            messages.success(request, "Fallback image removed successfully.")
            return redirect('admin_panel')

        # Copy POST data to populate missing fields from instance so validation doesn't fail
        post_data = request.POST.copy()
        if 'education_external_url' not in post_data:
            post_data['education_external_url'] = site_setting.education_external_url

        form = SiteSettingForm(post_data, request.FILES, instance=site_setting)
        if form.is_valid():
            site_setting = form.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})
                
            messages.success(request, "Platform branding and media settings updated successfully!")
            return redirect('admin_panel')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
            
            messages.error(request, "Please fix the errors below.")
            
    return redirect('admin_panel')

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
        # Mark the "Services Selected" milestone as APPROVED when the client confirms
        profile.services_selected_status = 'APPROVED'
        profile.save()
        # Keep the persisted RoadmapStep in sync immediately
        RoadmapStep.objects.filter(client=request.user, title__iexact='Services Selected').update(status='APPROVED')
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
@require_POST
def toggle_service(request, service_id):
    service = get_object_or_404(ServiceItem, id=service_id)
    
    client_id = request.GET.get('client_id') or request.POST.get('client_id')
    profile = None
    if client_id and request.user.is_staff:
        try:
            from django.contrib.auth.models import User
            user = User.objects.filter(id=client_id).first()
            if user:
                profile, _ = ClientProfile.objects.get_or_create(user=user)
            else:
                profile = get_object_or_404(ClientProfile, id=client_id)
        except (ValueError, TypeError):
            pass

    if not profile:
        profile, _ = ClientProfile.objects.get_or_create(user=request.user)

    if profile.selected_services.filter(id=service.id).exists():
        profile.selected_services.remove(service)
        selected = False
    else:
        profile.selected_services.add(service)
        selected = True
    profile.save()

    return JsonResponse({
        'status': 'success',
        'selected': selected,
        'active_count': profile.selected_services.count(),
        'service_id': service.id,
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
            messages.success(request, "Setup completed successfully! Welcome to Wisdom Tower.")
            return redirect('home')
            
    rules = [
        ("Contact Us Before Work Begins",
         "All project scopes, timelines, and deliverables must be agreed upon by contacting Wisdom Tower directly via phone, the Message Us form, or social media — before any work commences."),
        ("Provide a Valid Phone Number",
         "When sending a written inquiry via the Message Us form, you must include a reachable phone number. This allows our team to follow up and confirm your requirements efficiently."),
        ("Respect Agreed Timelines",
         "Once a project timeline is agreed upon, clients are expected to provide required materials, approvals, and feedback promptly. Delays caused by the client may affect the agreed delivery schedule."),
        ("No Unauthorized Redistribution",
         "Deliverables provided by Wisdom Tower are intended exclusively for the client's own use and may not be resold, redistributed, or sub-licensed without prior written permission."),
        ("Professional Communication",
         "All communication with the Wisdom Tower team should be conducted professionally and respectfully. Abusive or inappropriate behaviour may result in immediate termination of service."),
        ("Payment Discussion is Direct",
         "Pricing is never fixed — it is determined directly between you and our team based on scope, complexity, and timeline. We do not publish or enforce fixed rate cards; all quotes are custom."),
    ]
    return render(request, 'core/choose_pricing.html', {
        'profile': profile,
        'rules': rules,
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

    # Fetch persisted roadmap steps for the target user (if any)
    roadmap_steps = RoadmapStep.objects.filter(client=target_user).order_by('order')

    # Auto-initialize default steps if none exist (useful for existing users)
    if not roadmap_steps.exists():
        try:
            from .models import create_default_roadmap_steps
            create_default_roadmap_steps(target_user)
            roadmap_steps = RoadmapStep.objects.filter(client=target_user).order_by('order')
        except Exception:
            pass

    # Group selected services by category for organized display
    categories_map = dict(ServiceItem.CATEGORY_CHOICES)
    grouped_services = {}
    for svc in selected_services:
        cat_display = categories_map.get(svc.category, svc.category)
        if cat_display not in grouped_services:
            grouped_services[cat_display] = []
        grouped_services[cat_display].append(svc)

    # Compute progress percent from roadmap_steps
    total_steps = roadmap_steps.count()
    approved_steps = roadmap_steps.filter(status='APPROVED').count()
    progress_percent = int((approved_steps / total_steps) * 100) if total_steps > 0 else 0

    return render(request, 'core/client_dashboard.html', {
        'profile': profile,
        'dashboard_user': target_user,
        'selected_services': selected_services,
        'grouped_services': grouped_services,
        'onboarding_step': profile.onboarding_step,
        'project_lead_assigned': profile.project_lead_assigned or (profile.assigned_lead is not None),
        'active_sub_services': selected_services,
        'roadmap_steps': roadmap_steps,
        'progress_percent': progress_percent,
    })


class ClientAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id, *args, **kwargs):
        profile = get_object_or_404(ClientProfile, id=client_id)
        if not request.user.is_staff and profile.user != request.user:
            return Response({'error': 'Unauthorized'}, status=403)
        
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

VALID_MILESTONE_STATUSES = {'PENDING', 'APPROVED', 'DECLINED'}


def _resolve_milestone_field(profile, milestone_type=None):
    if milestone_type in {'services', 'services_selected_status'}:
        return 'services_selected_status'
    if milestone_type in {'team', 'team_assignment_status'}:
        return 'team_assignment_status'
    if milestone_type in {'kickoff', 'kickoff_call_status'}:
        return 'kickoff_call_status'
    if milestone_type in {'deliverables', 'deliverables_begin_status'}:
        return 'deliverables_begin_status'

    if profile.onboarding_step == 1:
        return 'services_selected_status'
    if profile.onboarding_step == 2:
        return 'team_assignment_status'
    if profile.onboarding_step == 3:
        return 'kickoff_call_status'
    if profile.onboarding_step == 4:
        return 'deliverables_begin_status'

    return 'services_selected_status'


def update_milestone_status(request, milestone_id, new_status):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseForbidden("Forbidden: Only staff members can update milestone statuses.")

    profile = get_object_or_404(ClientProfile, id=milestone_id)
    milestone_type = request.GET.get('type') or request.POST.get('milestone_field')
    normalized_status = (new_status or '').upper()

    if normalized_status not in VALID_MILESTONE_STATUSES:
        return JsonResponse({'error': 'Invalid status'}, status=400)

    field_name = _resolve_milestone_field(profile, milestone_type)
    setattr(profile, field_name, normalized_status)
    profile.save()

    return JsonResponse({
        'status': 'success',
        'message': f"Milestone status updated to {normalized_status}.",
        'progress': profile.onboarding_progress_percentage,
        'field': field_name,
        'new_status': normalized_status,
    })


@login_required
@require_POST
def update_roadmap_status(request, step_id):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    profile = get_object_or_404(ClientProfile, id=step_id)
    new_status = (request.POST.get('status') or '').upper()
    milestone_type = request.POST.get('milestone_field') or request.POST.get('field') or request.POST.get('step_key') or request.GET.get('type')

    if new_status not in VALID_MILESTONE_STATUSES:
        return JsonResponse({'error': 'Invalid status'}, status=400)

    field_name = _resolve_milestone_field(profile, milestone_type)
    setattr(profile, field_name, new_status)
    profile.save()

    return JsonResponse({
        'status': 'success',
        'step_id': profile.id,
        'field': field_name,
        'new_status': new_status,
    })


def _sync_roadmap_step_to_profile(step):
    profile, _ = ClientProfile.objects.get_or_create(user=step.client)
    title_lower = step.title.lower()
    if 'services selected' in title_lower:
        profile.services_selected_status = step.status
    elif 'team assignment' in title_lower:
        profile.team_assignment_status = step.status
    elif 'kickoff call' in title_lower:
        profile.kickoff_call_status = step.status
    elif 'deliverables begin' in title_lower:
        profile.deliverables_begin_status = step.status
    profile.save()


def _sync_profile_to_roadmap_steps(profile):
    mapping = {
        'services_selected_status': 'Services Selected',
        'team_assignment_status': 'Team Assignment',
        'kickoff_call_status': 'Kickoff Call',
        'deliverables_begin_status': 'Deliverables Begin',
    }
    for field, title in mapping.items():
        status = getattr(profile, field)
        if status == 'APPROVED':
            RoadmapStep.objects.filter(client=profile.user, title__iexact=title).update(status='APPROVED')
        elif status == 'DECLINED':
            RoadmapStep.objects.filter(client=profile.user, title__iexact=title).update(status='DECLINED')
        else:
            RoadmapStep.objects.filter(client=profile.user, title__iexact=title).update(status='PENDING')


@login_required
@require_POST
def update_roadmap_step_status(request, step_id):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    step = get_object_or_404(RoadmapStep, id=step_id)
    new_status = (request.POST.get('status') or '').upper()

    if new_status in {'APPROVED', 'DECLINED', 'PENDING'}:
        step.status = new_status
        step.save()
        _sync_roadmap_step_to_profile(step)
        
        # Calculate updated progress metrics to return to the caller
        client_steps = RoadmapStep.objects.filter(client=step.client)
        total_count = client_steps.count()
        approved_count = client_steps.filter(status='APPROVED').count()
        progress_percent = int((approved_count / total_count) * 100) if total_count > 0 else 0
        
        return JsonResponse({
            'status': 'success',
            'new_status': step.status,
            'step_id': step.id,
            'progress_percent': progress_percent,
            'approved_count': approved_count,
            'total_count': total_count,
            'client_user_id': step.client.id,
        })

    return JsonResponse({'error': 'Invalid status'}, status=400)


@login_required
@require_POST
def toggle_roadmap_step(request, step_id):
    step = get_object_or_404(RoadmapStep, id=step_id)
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized: Admin access required.'}, status=403)

    step.status = 'DECLINED' if step.status == 'APPROVED' else 'APPROVED'
    step.save()
    _sync_roadmap_step_to_profile(step)

    client_steps = RoadmapStep.objects.filter(client=step.client)
    total_count = client_steps.count()
    approved_count = client_steps.filter(status='APPROVED').count()
    progress_percent = int((approved_count / total_count) * 100) if total_count > 0 else 0

    return JsonResponse({
        'status': 'success',
        'step_id': step.id,
        'new_status': step.status,
        'progress_percent': progress_percent,
        'approved_count': approved_count,
        'total_count': total_count,
        'client_user_id': step.client.id,
    })


@login_required
@require_POST
def roadmap_update_status_api(request):
    """
    Fine-grained 3-state roadmap step control for admin use.
    Accepts JSON body: { "step_id": <int>, "status": "APPROVED"|"DECLINED"|"PENDING" }
    Returns JSON with updated step info and recalculated progress.
    Staff-only: returns 403 for non-staff users.
    """
    import json
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized: Admin access required.'}, status=403)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

    step_id = payload.get('step_id')
    new_status = (payload.get('status') or '').upper()

    if not step_id:
        return JsonResponse({'error': 'Missing step_id.'}, status=400)

    if new_status not in {'APPROVED', 'DECLINED', 'PENDING'}:
        return JsonResponse({'error': f'Invalid status "{new_status}". Must be APPROVED, DECLINED, or PENDING.'}, status=400)

    step = get_object_or_404(RoadmapStep, id=step_id)
    step.status = new_status
    step.save()
    _sync_roadmap_step_to_profile(step)

    client_steps = RoadmapStep.objects.filter(client=step.client)
    total_count = client_steps.count()
    approved_count = client_steps.filter(status='APPROVED').count()
    progress_percent = int((approved_count / total_count) * 100) if total_count > 0 else 0

    return JsonResponse({
        'status': 'success',
        'step_id': step.id,
        'new_status': step.status,
        'progress_percent': progress_percent,
        'approved_count': approved_count,
        'total_count': total_count,
        'client_user_id': step.client.id,
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
            _sync_profile_to_roadmap_steps(profile)
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
    _sync_profile_to_roadmap_steps(profile)
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
    GET  /api/metric-entries/?client_username=X[&sub_service_id=Y][&period=week|month|year]
         Returns per-service aggregated totals (week / month / year) PLUS
         the ordered daily points for sparkline rendering.

    POST /api/metric-entries/
         Body (JSON): { client_username, sub_service_id, value, date, note }
         Creates or updates the ClientMetricEntry for that client+sub_service+date.
         Superuser / staff only.
    """
    from .models import ClientMetricEntry, SubService
    from django.db.models import Sum
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
        sub_service_id  = data.get('sub_service_id')
        value_raw       = data.get('value')
        date_str        = data.get('date', '').strip()
        note            = data.get('note', '').strip()

        if not client_username or not sub_service_id or value_raw is None:
            return JsonResponse(
                {'status': 'error', 'message': 'client_username, sub_service_id, and value are required.'},
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
            sub_service = SubService.objects.get(id=sub_service_id)
        except SubService.DoesNotExist:
            return JsonResponse(
                {'status': 'error', 'message': f'No sub-service with id "{sub_service_id}".'},
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

        entry, created = ClientMetricEntry.objects.update_or_create(
            client=client,
            sub_service=sub_service,
            date=entry_date,
            defaults={'value': value, 'note': note}
        )

        try:
            from .models import create_notification
            action_word = "added" if created else "updated"
            create_notification(
                recipients=client,
                title="Analytics Metric Updated",
                message=f"Admin has {action_word} a data point for '{sub_service.title}' on {entry_date.strftime('%Y-%m-%d')}.",
                notification_type="metric_update"
            )
        except Exception:
            pass

        return JsonResponse({
            'status': 'created' if created else 'updated',
            'entry': {
                'id':             entry.id,
                'client':         client.username,
                'sub_service_id': entry.sub_service.id,
                'value':          entry.value,
                'date':           entry.date.strftime('%Y-%m-%d'),
                'note':           entry.note,
                'last_updated':   entry.last_updated.isoformat() if entry.last_updated else None
            }
        })

    # ── GET: Return aggregated data per service ───────────────────────────────
    client_username = request.GET.get('client_username', '').strip()
    sub_service_id  = request.GET.get('sub_service_id')
    date_query      = request.GET.get('date', '').strip()
    start_date      = request.GET.get('start_date', '').strip()
    end_date        = request.GET.get('end_date', '').strip()

    if not client_username:
        return JsonResponse({'status': 'error', 'message': 'client_username is required.'}, status=400)

    # 1. State-aware single date value query for form pre-populating
    if sub_service_id and date_query:
        try:
            entry = ClientMetricEntry.objects.get(
                client__username=client_username,
                sub_service_id=sub_service_id,
                date=date_query
            )
            return JsonResponse({
                'status': 'success',
                'value': entry.value,
                'note': entry.note,
                'last_updated': entry.last_updated.isoformat() if entry.last_updated else None
            })
        except ClientMetricEntry.DoesNotExist:
            return JsonResponse({
                'status': 'success',
                'value': 0.0,
                'note': '',
                'last_updated': None
            })

    # 2. General aggregated service metric query
    qs = ClientMetricEntry.objects.filter(client__username=client_username).select_related('sub_service').order_by('date')

    if sub_service_id:
        qs = qs.filter(sub_service_id=sub_service_id)
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

    today = date_type.today()

    # Pre-compute period boundaries once
    from datetime import timedelta
    week_start  = today - timedelta(days=today.weekday())
    week_end    = week_start + timedelta(days=6)
    month_start = today.replace(day=1)
    year_start  = today.replace(month=1, day=1)

    service_map = {}   # { sub_service_id: { sub_service_name, week_total, month_total, year_total, daily_points, last_updated } }

    for entry in qs:
        sub_svc = entry.sub_service
        sub_svc_id = sub_svc.id
        if sub_svc_id not in service_map:
            service_map[sub_svc_id] = {
                'sub_service_name': sub_svc.name,
                'week_total':  0.0,
                'month_total': 0.0,
                'year_total':  0.0,
                'daily_points': [],
                'last_updated': None,
            }
        rec = service_map[sub_svc_id]

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
    Returns a list of active sub-services that are currently approved
    for the client. Filters by the milestone status (services_selected_status == 'APPROVED').
    """
    from django.contrib.auth.models import User
    from .models import ClientProfile, SubService

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
        services_list = []
        for entry in profile.selected_services.all():
            services_list.append({
                'id': entry.id,
                'name': entry.name,
                'category': entry.category
            })
        return JsonResponse({'status': 'success', 'services': services_list})
    else:
        return JsonResponse({'status': 'success', 'services': []})


@csrf_exempt
def add_team_member_inline(request):
    """
    Staff-only endpoint to create or update a TeamMember (leader) via AJAX/FormData without leaving the page.
    Accepts multipart/form-data (avatar file upload) or JSON body.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse({'status': 'error', 'message': 'Forbidden: Staff access required.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed.'}, status=405)

    # Resolve data source: prefer multipart form data, fall back to JSON body
    content_type = request.content_type or ''
    if 'multipart' in content_type or 'application/x-www-form-urlencoded' in content_type:
        data = request.POST
    else:
        import json
        try:
            data = json.loads(request.body)
        except (ValueError, TypeError):
            data = request.POST

    member_id = data.get('id')
    name = (data.get('name') or '').strip()
    job_role = (data.get('job_role') or '').strip()
    bio = (data.get('bio') or '').strip()
    order_val = data.get('order', 0)
    avatar_file = request.FILES.get('avatar')

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
            member.order = order
            if avatar_file:
                member.image = avatar_file
            member.save()
            action = 'updated'
        except TeamMember.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Leader not found.'}, status=404)
    else:
        member = TeamMember(
            name=name,
            job_role=job_role,
            bio=bio,
            order=order
        )
        if avatar_file:
            member.image = avatar_file
        member.save()
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
    Falls back to a hardcoded catalog if the ServiceCategory table is empty.
    """
    categories = ServiceCategory.objects.all().prefetch_related('subservices').order_by('order')
    selected_service_ids = []
    
    # ── Grab client_id parameter if requested by staff ──
    client_id = request.GET.get('client_id')
    target_profile = None
    if client_id and request.user.is_authenticated and request.user.is_staff:
        try:
            from django.contrib.auth.models import User
            user = User.objects.filter(id=client_id).first()
            if user:
                target_profile = ClientProfile.objects.filter(user=user).first()
            else:
                target_profile = ClientProfile.objects.filter(id=client_id).first()
        except (ValueError, TypeError):
            pass

    if target_profile:
        selected_service_ids = list(target_profile.selected_services.values_list('id', flat=True))
    elif request.user.is_authenticated:
        profile, _ = ClientProfile.objects.get_or_create(user=request.user)
        selected_service_ids = list(profile.selected_services.values_list('id', flat=True))

    # --- Fallback: if the DB catalog is empty, provide hardcoded Wisdom Tower categories ---
    fallback_categories = []
    if not categories.exists():
        fallback_categories = [
            {
                'title': 'Graphic & Print Design',
                'icon_class': 'fas fa-palette',
                'description': 'Visual identity crafted for print and digital impact.',
                'subservices': [
                    'Visual communication & brand identity',
                    'Presentation slide design (PowerPoint, Google Slides, Canva)',
                    'Book covers & eBook design',
                    'Resume/CV design',
                    'Posters, flyers, brochures & leaflets',
                    'Business cards, stickers & digital artwork',
                ],
            },
            {
                'title': 'Writing & Editorial',
                'icon_class': 'fas fa-pen-nib',
                'description': 'Words that persuade, inform, and convert.',
                'subservices': [
                    'Article and blog writing',
                    'Website content writing',
                    'Copywriting (ads, product descriptions)',
                    'Scriptwriting (YouTube, podcasts, short films)',
                    'Speech writing & creative fiction stories',
                    'Technical writing, proposal & grant writing',
                    'Editing, proofreading, rewriting & paraphrasing',
                ],
            },
            {
                'title': 'Academic & Research Support',
                'icon_class': 'fas fa-graduation-cap',
                'description': 'Rigorous research and academic formatting.',
                'subservices': [
                    'Thesis & dissertation writing support',
                    'Academic editing & formatting (APA, MLA, Chicago, Vancouver)',
                    'Research summaries, proposals & abstracts',
                    'Referencing & citation management',
                    'Plagiarism checking & reduction',
                    'PowerPoint presentations for research defense',
                ],
            },
            {
                'title': 'Data & Tech Solutions',
                'icon_class': 'fas fa-database',
                'description': 'Custom web software, APIs, and analytics engineering.',
                'subservices': [
                    'Custom website & web app development',
                    'E-commerce & business system development',
                    'API integration & backend systems',
                    'Data analysis & business intelligence dashboards',
                    'Automation & workflow scripting',
                    'Digital tools & SaaS product consulting',
                ],
            },
            {
                'title': 'Web & Digital Marketing',
                'icon_class': 'fas fa-bullhorn',
                'description': 'Strategies that grow traffic, leads, and conversions.',
                'subservices': [
                    'SEO strategy & implementation',
                    'Social media management & content calendars',
                    'Paid advertising (Google Ads, Meta Ads)',
                    'Email marketing campaigns',
                    'Content strategy & editorial planning',
                    'Influencer and affiliate marketing coordination',
                ],
            },
            {
                'title': 'Business Strategy & Admin',
                'icon_class': 'fas fa-briefcase',
                'description': 'Professional frameworks to grow and manage your enterprise.',
                'subservices': [
                    'Business plan writing',
                    'Market research & competitor analysis',
                    'Financial modeling & projections',
                    'Virtual assistant services',
                    'HR & recruitment consulting',
                    'Startup advisory & pitch deck creation',
                ],
            },
            {
                'title': 'Education & Multimedia',
                'icon_class': 'fas fa-chalkboard-teacher',
                'description': 'Interactive e-learning content and instructional media.',
                'subservices': [
                    'E-learning course creation',
                    'Instructional video production & editing',
                    'Motion graphics & animated explainers',
                    'Training materials & workshop content',
                    'Podcast editing & audio production',
                    'YouTube channel management & content strategy',
                ],
            },
        ]

    return render(request, 'core/services.html', {
        'categories': categories,
        'fallback_categories': fallback_categories,
        'selected_service_ids': selected_service_ids,
        'site_settings': SiteSetting.objects.first(),
    })


def experience_page(request):
    """
    Experience page rendering Project entries grouped by the standardized ProjectCategory values.
    This ensures the public experience showcase reflects admin-managed portfolio projects
    and the custom Admin Command Center upload form.
    """
    ProjectCategory.ensure_standard_categories()
    standard_slugs = [slug for slug, _, _ in ProjectCategory.STANDARD_CATEGORIES]
    project_categories = ProjectCategory.objects.filter(slug__in=standard_slugs).order_by('order')
    project_groups = []
    for category in project_categories:
        projects = category.projects.all().order_by('-created_at')
        if category.slug == 'video-experience':
            for project in projects:
                project.is_playable = bool(project.video)
        project_groups.append({
            'category': category,
            'projects': projects,
        })

    return render(request, 'core/experience.html', {
        'project_categories': project_categories,
        'project_groups': project_groups,
    })



