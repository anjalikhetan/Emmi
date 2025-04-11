import uuid
from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.core.validators import MinValueValidator, MaxValueValidator


class Plan(models.Model):
    """
    Model representing a training plan for a user.
    
    A plan is associated with a single user and contains training information
    in the plan_info JSONField. It can have multiple workouts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        related_name='plans'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    generation_completed_at = models.DateTimeField(null=True, blank=True)
    generation_error = models.TextField(null=True, blank=True)
    plan_info = models.JSONField(null=True, blank=True)
    
    class Meta:
        """Meta options for the Plan model."""
        ordering = ['-created_at']
    
    def __str__(self):
        """String representation of the Plan model."""
        return f"Plan for {self.user.email}"
    
    def clean(self):
        """Validate the model as a whole."""
        super().clean()
        # Additional validation can be added here if needed
    
    def save(self, *args, **kwargs):
        """Override save to ensure model validation before saving."""
        self.full_clean()
        super().save(*args, **kwargs)
        
    @property
    def status(self):
        """
        Determines the status of the plan based on generation state.
        """
        if self.generation_error:
            return "error"
        elif self.generation_completed_at:
            return "completed"
        else:
            return "in progress"
    
    def set_error(self, error_message):
        """
        Sets an error message for the plan and clears generation_completed_at.
        This ensures the status is marked as 'error'.
        """
        self.generation_error = error_message
        self.generation_completed_at = None
        self.save()

    def mark_as_completed(self):
        """
        Marks the plan as completed by setting generation_completed_at to the current datetime.
        Clears any previous error.
        """
        self.generation_completed_at = now()
        self.generation_error = None
        self.save()


class Workout(models.Model):
    """
    Model representing a workout within a training plan.
    
    A workout is associated with a single plan and has a date,
    completion status, and details in the workout_info JSONField.
    """
    class CompletionStatus(models.TextChoices):
        COMPLETED = "completed", "Completed as planned"
        MODIFIED = "modified", "Modified"
        SKIPPED = "skipped", "Skipped"
        NOT_COMPLETED = "not_completed", "Not completed"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(
        'Plan',
        on_delete=models.CASCADE,
        related_name='workouts'
    )
    date = models.DateField()
    workout_info = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    completion_status = models.CharField(
        max_length=20,
        choices=CompletionStatus.choices,
        default=CompletionStatus.NOT_COMPLETED,
    )
    
    difficulty = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True,  # optional, in case it's not always provided
        blank=True
    )
    
    additional_notes = models.TextField(null=True, blank=True)
    
    class Meta:
        """Meta options for the Workout model."""
        ordering = ['-created_at']
    
    def __str__(self):
        """String representation of the Workout model."""
        return f"Workout {self.id} on {self.date} for {self.plan.user.email}"
    
    def clean(self):
        """Validate the model as a whole."""
        super().clean()
        # Additional validation can be added here if needed
    
    def save(self, *args, **kwargs):
        """Override save to ensure model validation before saving."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    class Meta:
        """Meta options for the Workout model."""
        ordering = ['date']