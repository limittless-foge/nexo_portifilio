from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user} - {self.rating} Stars"

    class Meta:
        ordering = ['-created_at']

class ContactMessage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,
        blank=True
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.user} - {self.subject}"

    class Meta:
        ordering = ['-created_at']

class Service(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon_class = models.CharField(max_length=50, help_text="FontAwesome icon class")
    header_image = models.URLField(max_length=500, blank=True, null=True, help_text="URL to professional header image")
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']

class ProjectCategory(models.Model):
    STANDARD_CATEGORIES = [
        ('video-experience', 'Video Experience', 0),
        ('web-experience', 'Web Experience', 1),
        ('design', 'Design & Creative', 2),
        ('marketing', 'Marketing & Strategy', 3),
        ('data-tech', 'Data & Tech Solutions', 4),
    ]

    name = models.CharField(max_length=100, unique=True, help_text="Project category name")
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Project Category"
        verbose_name_plural = "Project Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @classmethod
    def ensure_standard_categories(cls):
        for slug, name, order in cls.STANDARD_CATEGORIES:
            category, created = cls.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'order': order}
            )
            if not created and (category.name != name or category.order != order):
                category.name = name
                category.order = order
                category.save(update_fields=['name', 'order'])

class Project(models.Model):
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=50, blank=True)
    category_fk = models.ForeignKey(ProjectCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    MEDIA_TYPE_CHOICES = [
        ('VIDEO', 'Video'),
        ('IMAGE', 'Image'),
        ('OTHER', 'Other'),
    ]
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='OTHER')
    image_url = models.URLField(max_length=500, blank=True, null=True) # Keeping for legacy/external links
    image = models.ImageField(upload_to="project_images/", null=True, blank=True)
    video = models.FileField(upload_to="project_videos/", null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    technology_stack = models.CharField(max_length=200, blank=True, null=True, help_text="Comma separated tags e.g. Django, React, AWS")
    case_study_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def category_display(self):
        if self.category_fk:
            return self.category_fk.name
        return self.category or "General"

    def save(self, *args, **kwargs):
        if self.video:
            self.media_type = 'VIDEO'
        elif self.image or self.image_url:
            self.media_type = 'IMAGE'
        else:
            self.media_type = self.media_type or 'OTHER'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class ExperienceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Category name e.g. Video, Web, Design, Marketing")
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    icon = models.CharField(max_length=50, default='fas fa-folder', help_text="FontAwesome icon class")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Experience Category"
        verbose_name_plural = "Experience Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Experience(models.Model):
    title = models.CharField(max_length=150)
    category = models.ForeignKey(ExperienceCategory, on_delete=models.CASCADE, related_name='experiences')
    image_url = models.URLField(max_length=500, blank=True, null=True)
    image = models.ImageField(upload_to="experience_images/", null=True, blank=True)
    video = models.FileField(upload_to="experience_videos/", null=True, blank=True)
    video_url = models.URLField(max_length=500, blank=True, null=True, help_text="URL to video stream or external video link")
    description = models.TextField(blank=True, null=True)
    technology_stack = models.CharField(max_length=200, blank=True, null=True, help_text="Comma separated tags e.g. Premiere Pro, 4K Cinema, Motion Graphics")
    case_study_url = models.URLField(blank=True, null=True)
    is_featured = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Experience Item"
        verbose_name_plural = "Experience Items"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.category.name}] {self.title}"


class PhoneNumber(models.Model):
    site_setting = models.ForeignKey('SiteSetting', related_name='phone_numbers', on_delete=models.CASCADE)
    number = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.number

    class Meta:
        ordering = ['created_at']


class SiteSetting(models.Model):
    our_story_video = models.FileField(upload_to='site_videos/', blank=True, null=True)
    our_story_image = models.ImageField(upload_to='site_images/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    education_external_url = models.URLField(
        max_length=500, 
        default="https://example.com", 
        help_text="Dynamic link for Education & Multimedia card"
    )
    header_phone_number = models.CharField(
        max_length=30, 
        default="+251 968 929 372", 
        blank=True, 
        null=True,
        help_text="Phone number displayed in header (Leave empty or delete to remove)"
    )

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Global Site Settings"

    @classmethod
    def get_instance(cls):
        """Return the single SiteSetting instance, creating it with defaults if needed."""
        instance = cls.objects.first()
        if instance:
            return instance
        # Create with defaults from field definitions
        defaults = {}
        for field in cls._meta.fields:
            if field.has_default():
                # call default if callable
                defaults[field.name] = field.get_default()
        instance = cls.objects.create(**{k: v for k, v in defaults.items() if k != 'id'})
        return instance
class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    job_role = models.CharField(max_length=100)
    bio = models.TextField(blank=True, null=True, help_text="Short bio / description of the team leader")
    image = models.ImageField(upload_to='team_images/', null=True, blank=True)
    image_url = models.URLField(max_length=500, blank=True, null=True, help_text="Direct image URL if not using file upload")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def role(self):
        return self.job_role

    @property
    def image_display(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return None

    def __str__(self):
        return f"{self.name} - {self.job_role}"

    class Meta:
        ordering = ['order']
Leader = TeamMember


class ServiceCategory(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon_class = models.CharField(max_length=50, default="fas fa-cubes", help_text="FontAwesome icon class")
    header_image = models.URLField(max_length=500, blank=True, null=True, help_text="URL to professional header image")
    order = models.PositiveIntegerField(default=0)
    is_external_link = models.BooleanField(default=False)
    external_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']


class SubService(models.Model):
    CATEGORY_CHOICES = [
        ('DESIGN', 'Graphic & Print Design'),
        ('WRITING', 'Writing & Editorial'),
        ('ACADEMIC', 'Academic & Research Support'),
        ('DATA_TECH', 'Data & Tech Solutions'),
        ('MARKETING', 'Web & Digital Marketing'),
        ('BUSINESS', 'Business Strategy & Admin'),
        ('MULTIMEDIA', 'Education & Multimedia'),
    ]
    service_category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='subservices', null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=150)
    short_explanation = models.TextField()

    @property
    def name(self):
        return self.title

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"

    class Meta:
        db_table = 'core_serviceitem'

ServiceItem = SubService


class ClientProfile(models.Model):
    ONBOARDING_STEPS = [
        (1, 'Services Selected'),
        (2, 'Team Assignment'),
        (3, 'Kickoff Call'),
        (4, 'Deliverables Begin'),
    ]

    STAGE_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DECLINED', 'Declined / Restricted'),
    ]

    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='nexo_profile')
    registration_date = models.DateTimeField(auto_now_add=True, null=True, blank=True, help_text="Tracks when the client profile/account was created")
    selected_services = models.ManyToManyField('SubService', blank=True, related_name='selected_by_clients')
    chosen_tier = models.CharField(max_length=50, blank=True, null=True)
    onboarding_completed = models.BooleanField(default=False)
    project_lead_assigned = models.BooleanField(default=False, help_text="Designates if a project lead has been assigned to the client")
    onboarding_step = models.PositiveSmallIntegerField(
        choices=ONBOARDING_STEPS,
        default=1,
        help_text="Current step in the onboarding timeline"
    )
    assigned_lead = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_clients',
        help_text="Assigned project lead (staff member)"
    )

    # Roadmap Stage Validation Statuses
    services_selected_status = models.CharField(
        max_length=20,
        choices=STAGE_STATUS_CHOICES,
        default='PENDING',
        help_text="Status of the services selection step"
    )
    team_assignment_status = models.CharField(
        max_length=20,
        choices=STAGE_STATUS_CHOICES,
        default='PENDING',
        help_text="Status of the team assignment step"
    )
    kickoff_call_status = models.CharField(
        max_length=20,
        choices=STAGE_STATUS_CHOICES,
        default='PENDING',
        help_text="Status of the kickoff call step"
    )
    deliverables_begin_status = models.CharField(
        max_length=20,
        choices=STAGE_STATUS_CHOICES,
        default='PENDING',
        help_text="Status of the deliverables beginning step"
    )
    last_updated = models.DateTimeField(auto_now=True, help_text="Timestamp of the last status update")

    @property
    def approved_milestones_count(self):
        return self.user.roadmap_steps.filter(status='APPROVED').count()

    @property
    def onboarding_progress_percentage(self):
        total_steps = self.user.roadmap_steps.count()
        if total_steps == 0:
            return 0
        return int((self.approved_milestones_count / total_steps) * 100)

    @property
    def all_milestones_approved(self):
        total_steps = self.user.roadmap_steps.count()
        if total_steps == 0:
            return False
        return self.approved_milestones_count == total_steps

    @property
    def milestones_list(self):
        return [
            {
                'id': 'services',
                'name': 'Services Selected',
                'status': self.services_selected_status,
                'description': 'Service catalog confirmed',
                'step_number': 1
            },
            {
                'id': 'team',
                'name': 'Team Assignment',
                'status': self.team_assignment_status,
                'description': 'Project lead allocation',
                'step_number': 2
            },
            {
                'id': 'kickoff',
                'name': 'Kickoff Call',
                'status': self.kickoff_call_status,
                'description': 'Initial roadmap mapping',
                'step_number': 3
            },
            {
                'id': 'deliverables',
                'name': 'Deliverables Begin',
                'status': self.deliverables_begin_status,
                'description': 'Execution and delivery start',
                'step_number': 4
            }
        ]

    def __str__(self):
        return f"Profile of {self.user.username}"


class RoadmapStep(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DECLINED', 'Declined'),
    ]

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    client = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='roadmap_steps')
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()}) for {self.client.username}"


# Default roadmap steps used to initialize new client profiles
DEFAULT_ROADMAP_STEPS = [
    {'title': 'Services Selected', 'description': 'Service catalog confirmed', 'order': 1},
    {'title': 'Team Assignment', 'description': 'Project lead allocation', 'order': 2},
    {'title': 'Kickoff Call', 'description': 'Initial roadmap mapping', 'order': 3},
    {'title': 'Deliverables Begin', 'description': 'Execution and delivery start', 'order': 4},
]


def create_default_roadmap_steps(user):
    """Create the standard onboarding roadmap steps for a given user if they don't exist."""
    for step in DEFAULT_ROADMAP_STEPS:
        RoadmapStep.objects.get_or_create(
            client=user,
            title=step['title'],
            defaults={
                'description': step.get('description', ''),
                'order': step.get('order', 1),
                'status': 'PENDING',
            }
        )


@receiver(post_save, sender=ClientProfile)
def ensure_roadmap_steps_for_profile(sender, instance, created, **kwargs):
    """Ensure default roadmap steps exist whenever a ClientProfile is created."""
    if created:
        try:
            create_default_roadmap_steps(instance.user)
        except Exception:
            # Do not raise during signal handling; log silently in production
            pass


class ClientActivityLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('select_service', 'Selected Service'),
        ('update_profile', 'Updated Profile'),
        ('file_upload', 'Uploaded File'),
        ('view_dashboard', 'Viewed Dashboard'),
    ]

    client = models.ForeignKey(
        ClientProfile, 
        on_delete=models.CASCADE, 
        related_name='activity_logs'
    )
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True, null=True, help_text="Additional details about the action")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['client', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.client.user.username} - {self.get_action_type_display()} at {self.timestamp}"


@receiver(post_save, sender=User)
def handle_user_profile(sender, instance, created, **kwargs):
    if created:
        ClientProfile.objects.get_or_create(user=instance)
    else:
        if hasattr(instance, 'nexo_profile'):
            instance.nexo_profile.save()
        else:
            ClientProfile.objects.get_or_create(user=instance)


class ServiceAnalytics(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_analytics')
    service_name = models.CharField(max_length=100)
    metric_name = models.CharField(max_length=100, default='Value')
    metric_value = models.FloatField()
    date = models.DateField()
    explanation = models.TextField()

    class Meta:
        verbose_name = "Service Analytics"
        verbose_name_plural = "Service Analytics"
        ordering = ['-date']

    def __str__(self):
        return f"{self.client.username} - {self.service_name} - {self.metric_name}: {self.metric_value} ({self.date})"


# ─────────────────────────────────────────────────────────────────────────────
# ClientMetricEntry: single source of truth for service performance analytics.
# Admin enters only the DAILY value. Weekly/Monthly/Yearly totals are
# computed automatically via Django QuerySet aggregation at query time.
# ─────────────────────────────────────────────────────────────────────────────
class ClientMetricEntry(models.Model):
    client       = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='metric_entries',
        help_text="The client this metric belongs to."
    )
    sub_service  = models.ForeignKey(
        SubService,
        on_delete=models.CASCADE,
        related_name='metric_entries',
        help_text="The sub-service this metric belongs to."
    )
    value        = models.FloatField(
        help_text="Daily numeric value entered by the Admin (e.g. 5 videos produced)."
    )
    date         = models.DateField(
        help_text="The calendar date this entry refers to."
    )
    note         = models.TextField(
        blank=True,
        default='',
        help_text="Optional Admin note / explanation for this data point."
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="Tracks when the entry was created or last updated."
    )

    class Meta:
        verbose_name        = "Client Metric Entry"
        verbose_name_plural = "Client Metric Entries"
        ordering            = ['-date']
        db_table            = 'core_metricentry'
        # Prevent duplicate entries for the same client/sub-service/date
        unique_together     = ('client', 'sub_service', 'date')
        indexes = [
            models.Index(fields=['client', 'sub_service']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.client.username} | {self.sub_service.title} | {self.value} on {self.date}"

MetricEntry = ClientMetricEntry
