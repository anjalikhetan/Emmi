import uuid
import re
import logging
from pytz import all_timezones

from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

from phonenumber_field.modelfields import PhoneNumberField
from rest_framework.authtoken.models import Token

from api.users.validators import (
    validate_goals_list,
    validate_extra_training_list,
    validate_diet_list,
    validate_days_of_week_list,
    validate_past_problems_list,
)
from api.utils.mixpanel_service import MixpanelService


def validate_verification_code(value):
    """
    Validate that the verification code is exactly 6 digits.
    """
    if not re.match(r'^\d{6}$', value):
        raise ValidationError('Verification code must be exactly 6 digits.')


class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with an email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.username = email
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with an email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model with email as the unique identifier.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.username
    
    @property
    def current_plan(self):
        """
        Returns the current plan for the user.
        """
        return self.plans.first()


class Profile(models.Model):
    """
    User profile model with fitness and running information.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    timezone = models.CharField(
        max_length=100,
        choices=[(tz, tz) for tz in all_timezones],
        default='UTC'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        default=None
    )
    phone_number = PhoneNumberField(null=True, blank=True)
    is_onboarding_complete = models.BooleanField(default=False)
    
    # Basic information fields
    age = models.PositiveIntegerField(
        validators=[MinValueValidator(18), MaxValueValidator(120)],
        null=True,
        blank=True
    )
    
    # Height fields (imperial and metric)
    feet = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)],
        null=True,
        blank=True
    )
    inches = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(11)],
        null=True,
        blank=True
    )
    heightCm = models.FloatField(
        validators=[MinValueValidator(100), MaxValueValidator(250)],
        null=True,
        blank=True
    )
    
    # Weight fields (imperial and metric)
    weightKg = models.FloatField(
        validators=[MinValueValidator(10), MaxValueValidator(500)],
        null=True,
        blank=True
    )
    weightLbs = models.FloatField(
        validators=[MinValueValidator(22), MaxValueValidator(1100)],
        null=True,
        blank=True
    )
    
    # Goals and race information
    goals = models.JSONField(
        validators=[validate_goals_list],
        null=True,
        blank=True
    )
    goalsDetails = models.TextField(null=True, blank=True)
    
    # Race planning
    raceName = models.CharField(max_length=255, null=True, blank=True)
    raceDate = models.DateField(null=True, blank=True)
    distance = models.CharField(max_length=50, null=True, blank=True)
    timeGoal = models.CharField(max_length=50, null=True, blank=True)
    
    # Running experience
    runningExperience = models.TextField(null=True, blank=True)
    
    # Current routine
    routineDaysPerWeek = models.CharField(max_length=50, null=True, blank=True)
    routineMilesPerWeek = models.CharField(max_length=50, null=True, blank=True)
    routineEasyPace = models.CharField(max_length=50, null=True, blank=True)
    routineLongestRun = models.CharField(max_length=50, null=True, blank=True)
    
    # Race results and training details
    recentRaceResults = models.TextField(null=True, blank=True)
    
    # Additional training and diet
    extraTraining = models.JSONField(
        validators=[validate_extra_training_list],
        null=True,
        blank=True
    )
    diet = models.JSONField(
        validators=[validate_diet_list],
        null=True,
        blank=True
    )
    
    # Health and injury information
    injuries = models.TextField(null=True, blank=True)
    
    # Training schedule preferences
    daysCommitTraining = models.CharField(max_length=50, null=True, blank=True)
    preferredLongRunDays = models.JSONField(
        validators=[validate_days_of_week_list],
        null=True,
        blank=True
    )
    preferredWorkoutDays = models.JSONField(
        validators=[validate_days_of_week_list],
        null=True,
        blank=True
    )
    preferredRestDays = models.JSONField(
        validators=[validate_days_of_week_list],
        null=True,
        blank=True
    )
    
    # Additional information
    otherObligations = models.TextField(null=True, blank=True)
    pastProblems = models.JSONField(
        validators=[validate_past_problems_list],
        null=True,
        blank=True
    )
    moreInfo = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        Override save to ensure model validation before saving.
        Also track when onboarding is completed.
        """
        # Store current state of is_onboarding_complete before saving
        track_onboarding = False
        if self.pk:
            try:
                old_profile = Profile.objects.get(pk=self.pk)
                track_onboarding = (not old_profile.is_onboarding_complete and self.is_onboarding_complete)
            except Profile.DoesNotExist:
                # New profile being created with is_onboarding_complete=True
                track_onboarding = self.is_onboarding_complete
        else:
            # New profile being created with is_onboarding_complete=True
            track_onboarding = self.is_onboarding_complete
        
        # Perform standard validation and save
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Track onboarding completed event if flag went from False to True
        if track_onboarding:
            try:
                mixpanel_service = MixpanelService()
                mixpanel_service.track(
                    distinct_id=str(self.user.id),
                    event_name="Onboarding Completed"
                )
            except Exception as e:
                # Log error but continue with normal flow
                logging.error(f"Error tracking Onboarding Completed event: {str(e)}")

class PhoneVerification(models.Model):
    """
    Model to store phone verification codes.
    """
    phone_number = PhoneNumberField()
    verification_code = models.CharField(
        max_length=6,
        validators=[validate_verification_code]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Verification for {self.phone_number}"

    def clean(self):
        """
        Validate the model as a whole.
        """
        super().clean()
        # Additional validation can be added here if needed

    def save(self, *args, **kwargs):
        """
        Override save to ensure model validation.
        """
        self.full_clean()
        super().save(*args, **kwargs)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token_and_profile(
    sender, instance=None, created=False, **kwargs
):
    """
    Create a token and profile for the user when a new user is created.
    """
    if created:
        Token.objects.get_or_create(user=instance)
        Profile.objects.get_or_create(user=instance, defaults={'age': 30})