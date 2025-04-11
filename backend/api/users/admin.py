from datetime import datetime

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib import messages
from django_json_widget.widgets import JSONEditorWidget
from django.db import models
from django.db.models import OuterRef, Subquery, DateTimeField, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.html import format_html

from .models import User, Profile, PhoneVerification
from api.plans.models import Plan
from api.plans.services import TrainingPlanThreadManager


class ProfileInline(admin.StackedInline):
    """
    Profile inline for UserAdmin
    """
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    fieldsets = (
        ('Personal Information', {
            'fields': ('avatar', 'phone_number', 'age', 'is_onboarding_complete', 'timezone')
        }),
        ('Physical Characteristics', {
            'fields': (
                ('feet', 'inches', 'heightCm'),
                ('weightKg', 'weightLbs')
            ),
        }),
        ('Goals', {
            'fields': ('goals', 'goalsDetails')
        }),
        ('Race Information', {
            'fields': ('raceName', 'raceDate', 'distance', 'timeGoal')
        }),
        ('Running Experience', {
            'fields': ('runningExperience', 'recentRaceResults')
        }),
        ('Current Routine', {
            'fields': (
                'routineDaysPerWeek', 'routineMilesPerWeek',
                'routineEasyPace', 'routineLongestRun'
            )
        }),
        ('Health & Lifestyle', {
            'fields': ('extraTraining', 'diet', 'injuries', 'pastProblems')
        }),
        ('Schedule Preferences', {
            'fields': (
                'daysCommitTraining', 'preferredLongRunDays',
                'preferredWorkoutDays', 'preferredRestDays'
            )
        }),
        ('Additional Information', {
            'fields': ('otherObligations', 'moreInfo')
        }),
    )

class PlanInline(admin.TabularInline):
    """
    Inline admin for Plans within a User
    """
    model = Plan
    extra = 0
    fields = ('id', 'created_at', 'view_plan_link')
    readonly_fields = ('id', 'created_at', 'view_plan_link')

    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    def view_plan_link(self, obj):
        if obj.pk:
            url = reverse("admin:plans_plan_change", args=[obj.pk])  # Replace 'plans_plan' with your actual app and model names
            return format_html('<a href="{}">View Plan</a>', url)
        return "-"
    
    view_plan_link.short_description = "Plan Details"  # Sets column name in the admin panel


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    """
    User admin
    """
    inlines = (ProfileInline, PlanInline)
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_verified', 
                    'is_onboarding_complete', 'current_plan_id', 'current_plan_created_at')
    list_filter = ('is_verified', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    actions = ['generate_training_plan']

    fieldsets = DefaultUserAdmin.fieldsets + (
        ('Verification', {'fields': ('is_verified',)}),
    )

    def generate_training_plan(self, request, queryset):
        """
        Admin action to generate a training plan for selected users.
        """
        successful = 0
        failed = 0
        for user in queryset:
            try:
                # Check if user profile exists and is complete
                if not hasattr(user, 'profile') or not user.profile or not user.profile.is_onboarding_complete:
                    failed += 1
                    messages.warning(request, f"User {user.email} has an incomplete profile.")
                    continue
                
                # Check if a plan is already being generated
                if Plan.objects.filter(
                    user=user, 
                    generation_completed_at__isnull=True, 
                    generation_error__isnull=True
                ).exists():
                    failed += 1
                    messages.warning(request, f"A plan is already being generated for {user.email}.")
                    continue

                # Create a new plan
                plan = Plan.objects.create(user=user)
                
                # Start async generation
                TrainingPlanThreadManager().generate_training_plan_async(plan)

                successful += 1
                messages.success(request, f"Training plan generation started for {user.email} (Plan ID: {plan.id}).")
            
            except Exception as e:
                failed += 1
                messages.error(request, f"Failed to generate a plan for {user.email}: {str(e)}")
        
        if successful > 0:
            self.message_user(request, f"Successfully started {successful} training plan(s).", level=messages.SUCCESS)
        if failed > 0:
            self.message_user(request, f"{failed} training plan(s) could not be started.", level=messages.ERROR)

    generate_training_plan.short_description = "Generate Training Plan for selected users"

    def get_queryset(self, request):
        """
        Annotate the queryset to optimize and allow sorting by current_plan_created_at.
        Replace None values with a minimal date using Coalesce for correct sorting.
        """
        queryset = super().get_queryset(request)
        
        # Subquery to get the latest plan's created_at and id
        latest_plan_created_at_subquery = Plan.objects.filter(user=OuterRef('pk')).order_by('-created_at').values('created_at')[:1]
        latest_plan_id_subquery = Plan.objects.filter(user=OuterRef('pk')).order_by('-created_at').values('id')[:1]

        return queryset.annotate(
            current_plan_created_at=Coalesce(
                Subquery(latest_plan_created_at_subquery, output_field=DateTimeField()),
                Value(datetime(1900, 1, 1, 0, 0, 0), output_field=DateTimeField())
            ),
            current_plan_id=Subquery(latest_plan_id_subquery),
        )

    def is_onboarding_complete(self, obj):
        """
        Return whether the user has completed onboarding.
        """
        return obj.profile.is_onboarding_complete if hasattr(obj, 'profile') else False
    is_onboarding_complete.boolean = True
    is_onboarding_complete.admin_order_field = 'profile__is_onboarding_complete'

    def current_plan_id(self, obj):
        """
        Return the current plan ID.
        """
        return obj.current_plan.id if obj.current_plan else "-"
    current_plan_id.admin_order_field = 'current_plan_id'

    def current_plan_created_at(self, obj):
        """
        Return the creation date of the current plan.
        """
        if obj.current_plan:
            return obj.current_plan.created_at
        return "-"
    current_plan_created_at.admin_order_field = 'current_plan_created_at'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    """
    Phone Verification admin
    """
    list_display = ('phone_number', 'verification_code', 'created_at')
    search_fields = ('phone_number',)
    readonly_fields = ('created_at',)