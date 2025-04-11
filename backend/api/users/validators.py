"""
Custom validators for the user app models.
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_list_of_strings(value, field_name):
    """
    Generic function to validate that a given value is a list of strings.
    """
    if not isinstance(value, list):
        raise ValidationError(_(f"{field_name} must be a list."))

    if not all(isinstance(item, str) for item in value):
        raise ValidationError(_(f"All elements in {field_name} must be strings."))


def validate_goals_list(value):
    """
    Validate that the goals field is a list of strings.
    """
    validate_list_of_strings(value, "Goals")


def validate_extra_training_list(value):
    """
    Validate that the extraTraining field is a list of strings.
    """
    validate_list_of_strings(value, "Extra training")


def validate_diet_list(value):
    """
    Validate that the diet field is a list of strings.
    """
    validate_list_of_strings(value, "Diet")


def validate_days_of_week_list(value):
    """
    Validate that the field is a list of strings containing valid days of the week.
    """
    validate_list_of_strings(value, "Days")


def validate_past_problems_list(value):
    """
    Validate that the pastProblems field is a list of strings.
    """
    validate_list_of_strings(value, "Past problems")
