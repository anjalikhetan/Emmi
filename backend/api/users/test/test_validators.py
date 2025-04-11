from django.test import TestCase
from django.core.exceptions import ValidationError
from api.users.validators import (
    validate_goals_list,
    validate_extra_training_list,
    validate_diet_list,
    validate_days_of_week_list,
    validate_past_problems_list,
)

class TestValidators(TestCase):
    """
    Tests for the custom validators.
    """
    
    def test_validate_goals_list(self):
        """Test that goals list validator works correctly."""
        # Valid cases
        valid_goals = ["weight_loss", "improve_fitness", "run_faster"]
        validate_goals_list(valid_goals)  # Should not raise
        
        # Invalid cases
        with self.assertRaises(ValidationError):
            validate_goals_list("not a list")
        
        with self.assertRaises(ValidationError):
            validate_goals_list([1, 2, 3])
    
    def test_validate_extra_training_list(self):
        """Test that extra training list validator works correctly."""
        # Valid cases
        valid_activities = ["strength_training", "swimming", "none"]
        validate_extra_training_list(valid_activities)  # Should not raise
        
        # Invalid cases
        with self.assertRaises(ValidationError):
            validate_extra_training_list("not a list")
        
        with self.assertRaises(ValidationError):
            validate_extra_training_list([1, 2, 3])
    
    def test_validate_diet_list(self):
        """Test that diet list validator works correctly."""
        # Valid cases
        valid_diets = ["omnivore", "vegetarian", "vegan"]
        validate_diet_list(valid_diets)  # Should not raise
        
        # Invalid cases
        with self.assertRaises(ValidationError):
            validate_diet_list("not a list")
        
        with self.assertRaises(ValidationError):
            validate_diet_list([1, 2, 3])
    
    def test_validate_days_of_week_list(self):
        """Test that days of week list validator works correctly."""
        # Valid cases
        valid_days = ["monday", "wednesday", "friday"]
        validate_days_of_week_list(valid_days)  # Should not raise
        
        # Case insensitivity
        validate_days_of_week_list(["Monday", "Wednesday", "Friday"])  # Should not raise
        
        # Invalid cases
        with self.assertRaises(ValidationError):
            validate_days_of_week_list("not a list")
        
        with self.assertRaises(ValidationError):
            validate_days_of_week_list([1, 2, 3])
    
    def test_validate_past_problems_list(self):
        """Test that past problems list validator works correctly."""
        # Valid cases
        valid_problems = ["knee_pain", "shin_splints", "none"]
        validate_past_problems_list(valid_problems)  # Should not raise
        
        # Invalid cases
        with self.assertRaises(ValidationError):
            validate_past_problems_list("not a list")
        
        with self.assertRaises(ValidationError):
            validate_past_problems_list([1, 2, 3])
