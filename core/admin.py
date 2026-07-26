from django.contrib import admin
from django.db.models import Sum
from .models import (
    Review, ContactMessage, Project, ProjectCategory, Experience, ExperienceCategory,
    SiteSetting, TeamMember, ServiceItem, ClientProfile, ClientActivityLog,
    ServiceAnalytics, MetricEntry, ServiceCategory,
)


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_external_link', 'external_url')
    list_editable = ('is_external_link', 'external_url')
    search_fields = ('title', 'description')
    ordering = ('order',)


@admin.register(ExperienceCategory)
class ExperienceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_featured', 'created_at')
    list_filter = ('category', 'is_featured', 'created_at')
    search_fields = ('title', 'description', 'technology_stack')


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}



@admin.register(MetricEntry)
class MetricEntryAdmin(admin.ModelAdmin):
    """
    Admin UI for the MetricEntry model.

    The Admin enters only the daily VALUE for a given client + sub-service + date.
    Weekly / Monthly / Yearly totals are calculated on the fly by the API —
    no extra fields needed here.
    """
    list_display  = ('client', 'sub_service', 'value', 'date', 'note_preview')
    list_filter   = ('sub_service', 'date', 'client')
    search_fields = ('client__username', 'sub_service__title', 'note')
    date_hierarchy = 'date'
    ordering      = ('-date',)
    readonly_fields = ('week_total_display', 'month_total_display', 'year_total_display')

    fieldsets = (
        ('Entry Details', {
            'fields': ('client', 'sub_service', 'value', 'date', 'note')
        }),
        ('Computed Totals (read-only)', {
            'classes': ('collapse',),
            'description': 'These totals are calculated across ALL entries for this client + sub-service.',
            'fields': ('week_total_display', 'month_total_display', 'year_total_display'),
        }),
    )

    def note_preview(self, obj):
        return (obj.note[:60] + '…') if len(obj.note) > 60 else obj.note or '—'
    note_preview.short_description = 'Note'

    def _total_for(self, obj, period):
        from django.db.models.functions import TruncWeek, TruncMonth, TruncYear
        trunc_fn = {'week': TruncWeek, 'month': TruncMonth, 'year': TruncYear}[period]
        from datetime import date
        qs = MetricEntry.objects.filter(
            client=obj.client, sub_service=obj.sub_service
        )
        if period == 'week':
            from datetime import timedelta
            start = obj.date - timedelta(days=obj.date.weekday())
            end   = start + timedelta(days=6)
            qs = qs.filter(date__gte=start, date__lte=end)
        elif period == 'month':
            qs = qs.filter(date__year=obj.date.year, date__month=obj.date.month)
        else:
            qs = qs.filter(date__year=obj.date.year)
        total = qs.aggregate(t=Sum('value'))['t'] or 0
        return round(total, 2)

    def week_total_display(self, obj):
        return self._total_for(obj, 'week')
    week_total_display.short_description = 'Week Total (same week as entry date)'

    def month_total_display(self, obj):
        return self._total_for(obj, 'month')
    month_total_display.short_description = 'Month Total (same month as entry date)'

    def year_total_display(self, obj):
        return self._total_for(obj, 'year')
    year_total_display.short_description = 'Year Total (same year as entry date)'



@admin.register(ServiceAnalytics)
class ServiceAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('client', 'service_name', 'metric_name', 'metric_value', 'date')
    list_filter = ('date', 'service_name', 'metric_name')
    search_fields = ('client__username', 'service_name', 'metric_name', 'explanation')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'comment')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'subject', 'message')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    search_fields = ('title', 'category')

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('education_external_url', 'header_phone_number', 'phone_number')

    def has_add_permission(self, request):
        # Only allow one instance of SiteSetting
        return not SiteSetting.objects.exists()

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'job_role', 'order', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'job_role')
    ordering = ('order',)


@admin.register(ServiceItem)
class ServiceItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'service_category')
    list_filter = ('category', 'service_category')
    search_fields = ('title', 'category')


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'chosen_tier', 
        'onboarding_step', 
        'assigned_lead', 
        'onboarding_completed',
        'services_selected_status',
        'team_assignment_status',
        'kickoff_call_status',
        'deliverables_begin_status'
    )
    list_filter = (
        'chosen_tier', 
        'onboarding_step', 
        'onboarding_completed',
        'services_selected_status',
        'team_assignment_status',
        'kickoff_call_status',
        'deliverables_begin_status'
    )
    search_fields = ('user__username', 'user__email', 'chosen_tier', 'assigned_lead__username')
    filter_horizontal = ('selected_services',)
    fieldsets = (
        (None, {
            'fields': ('user', 'chosen_tier', 'onboarding_step', 'onboarding_completed', 'assigned_lead', 'project_lead_assigned')
        }),
        ('Selected Services', {
            'fields': ('selected_services',)
        }),
        ('Roadmap Approval Statuses', {
            'fields': (
                'services_selected_status',
                'team_assignment_status',
                'kickoff_call_status',
                'deliverables_begin_status'
            )
        }),
    )

    actions = [
        'approve_all_milestones',
        'approve_services_selected',
        'approve_team_assignment',
        'approve_kickoff_call',
        'approve_deliverables_begin',
        'decline_all_milestones'
    ]

    @admin.action(description="Mark all milestones as APPROVED")
    def approve_all_milestones(self, request, queryset):
        queryset.update(
            services_selected_status='APPROVED',
            team_assignment_status='APPROVED',
            kickoff_call_status='APPROVED',
            deliverables_begin_status='APPROVED'
        )
        self.message_user(request, "Selected client profiles have all milestones approved.")

    @admin.action(description="Mark 'Services Selected' as APPROVED")
    def approve_services_selected(self, request, queryset):
        queryset.update(services_selected_status='APPROVED')
        self.message_user(request, "Selected 'Services Selected' milestones approved.")

    @admin.action(description="Mark 'Team Assignment' as APPROVED")
    def approve_team_assignment(self, request, queryset):
        queryset.update(team_assignment_status='APPROVED')
        self.message_user(request, "Selected 'Team Assignment' milestones approved.")

    @admin.action(description="Mark 'Kickoff Call' as APPROVED")
    def approve_kickoff_call(self, request, queryset):
        queryset.update(kickoff_call_status='APPROVED')
        self.message_user(request, "Selected 'Kickoff Call' milestones approved.")

    @admin.action(description="Mark 'Deliverables Begin' as APPROVED")
    def approve_deliverables_begin(self, request, queryset):
        queryset.update(deliverables_begin_status='APPROVED')
        self.message_user(request, "Selected 'Deliverables Begin' milestones approved.")

    @admin.action(description="Reset/Mark all milestones as DECLINED")
    def decline_all_milestones(self, request, queryset):
        queryset.update(
            services_selected_status='DECLINED',
            team_assignment_status='DECLINED',
            kickoff_call_status='DECLINED',
            deliverables_begin_status='DECLINED'
        )
        self.message_user(request, "Selected client profiles have all milestones declined.")


@admin.register(ClientActivityLog)
class ClientActivityLogAdmin(admin.ModelAdmin):
    list_display = ('client', 'action_type', 'timestamp')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('client__user__username', 'description')
