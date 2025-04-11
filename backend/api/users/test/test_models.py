from django.test import TestCase
from django.core.exceptions import ValidationError
from phonenumber_field.phonenumber import PhoneNumber
from api.users.models import PhoneVerification, Profile
from api.users.test.factories import UserFactory, PhoneVerificationFactory
from unittest.mock import patch


class TestPhoneVerificationModel(TestCase):
    """
    Tests for the PhoneVerification model.
    """
    
    def setUp(self):
        self.phone_verification = PhoneVerificationFactory()
    
    def test_phone_verification_creation(self):
        """Test that a PhoneVerification instance can be created."""
        self.assertIsInstance(self.phone_verification, PhoneVerification)
        self.assertIsInstance(self.phone_verification.phone_number, PhoneNumber)
        self.assertEqual(len(self.phone_verification.verification_code), 6)
        self.assertTrue(self.phone_verification.verification_code.isdigit())
        self.assertIsNotNone(self.phone_verification.created_at)
    
    def test_invalid_phone_number_rejected(self):
        """Test that invalid phone numbers are rejected."""
        with self.assertRaises(Exception):
            PhoneVerification.objects.create(
                phone_number="invalid-phone",
                verification_code="123456"
            )
    
    def test_invalid_verification_code_length(self):
        """Test that verification codes must be exactly 6 digits."""
        # Test too short
        with self.assertRaises(Exception):
            self.phone_verification.verification_code = "12345"
            self.phone_verification.save()
        
        # Test too long
        with self.assertRaises(Exception):
            self.phone_verification.verification_code = "1234567"
            self.phone_verification.save()
    
    def test_phone_verification_string_representation(self):
        """Test the string representation of PhoneVerification objects."""
        self.assertEqual(
            str(self.phone_verification),
            f"Verification for {self.phone_verification.phone_number}"
        )


class TestProfileModel(TestCase):
    """
    Tests for the Profile model.
    """
    
    def setUp(self):
        self.user = UserFactory()
        self.profile = self.user.profile
        
    def test_profile_creation(self):
        """Test that a Profile is created for each User."""
        self.assertIsInstance(self.profile, Profile)
        self.assertEqual(str(self.profile.user.id), str(self.user.id))
        
    def test_profile_with_phone_number(self):
        """Test that a Profile can store a phone number."""
        phone_number = "+12025550109"  # Example US number
        self.profile.phone_number = phone_number
        self.profile.save()
        
        # Refresh from db
        self.profile.refresh_from_db()
        self.assertEqual(str(self.profile.phone_number), phone_number)
        
    def test_profile_with_invalid_phone_number(self):
        """Test that invalid phone numbers are rejected."""
        with self.assertRaises(Exception):
            self.profile.phone_number = "invalid-phone"
            self.profile.save()

    def test_age_validation(self):
        """Test that age must be within the valid range."""
        # Valid cases
        self.profile.age = 18
        self.profile.save()
        self.profile.age = 120
        self.profile.save()
        
        # Invalid cases
        with self.assertRaises(ValidationError):
            self.profile.age = 17
            self.profile.save()
        
        with self.assertRaises(ValidationError):
            self.profile.age = 121
            self.profile.save()
    
    def test_height_validation(self):
        """Test that height fields must be within valid ranges."""
        # Valid cases for feet and inches
        self.profile.feet = 5
        self.profile.inches = 10
        self.profile.save()

        # Invalid cases for feet
        with self.assertRaises(ValidationError):
            self.profile.feet = 0  # Min allowed is 1
            self.profile.save()

        with self.assertRaises(ValidationError):
            self.profile.feet = 9  # Max allowed is 8
            self.profile.save()

        # Reset feet to a valid value
        self.profile.feet = 5
        self.profile.save()

        # Invalid cases for inches
        with self.assertRaises(ValidationError):
            self.profile.inches = -1  # Min allowed is 0
            self.profile.save()

        with self.assertRaises(ValidationError):
            self.profile.inches = 12  # Max allowed is 11, so 12 should trigger a validation error
            self.profile.save()
    
    def test_weight_validation(self):
        """Test that weight fields must be within valid ranges."""
        # Valid cases
        self.profile.weightKg = 70.5
        self.profile.weightLbs = 155.3
        self.profile.save()
        
        # Invalid cases for weightKg
        with self.assertRaises(ValidationError):
            self.profile.weightKg = 9
            self.profile.save()
        
        with self.assertRaises(ValidationError):
            self.profile.weightKg = 501
            self.profile.save()
        
        # Reset weightKg
        self.profile.weightKg = 70.5
        self.profile.save()
        
        # Invalid cases for weightLbs
        with self.assertRaises(ValidationError):
            self.profile.weightLbs = 21
            self.profile.save()
        
        with self.assertRaises(ValidationError):
            self.profile.weightLbs = 1101
            self.profile.save()
    
    def test_goals_validation(self):
        """Test that goals must be a valid list of strings."""
        # Valid case
        self.profile.goals = ["weight_loss", "improve_fitness"]
        self.profile.save()
        
        # Invalid cases
        with self.assertRaises(ValidationError):
            self.profile.goals = "not a list"
            self.profile.save()
    
    def test_extra_training_validation(self):
        """Test that extraTraining must be a valid list of strings."""
        # Valid case
        self.profile.extraTraining = ["strength_training", "yoga"]
        self.profile.save()
        
        # Invalid cases
        with self.assertRaises(ValidationError):
            self.profile.extraTraining = "not a list"
            self.profile.save()
    
    def test_diet_validation(self):
        """Test that diet must be a valid list of strings."""
        # Valid case
        self.profile.diet = ["omnivore", "gluten_free"]
        self.profile.save()
        
        # Invalid cases
        with self.assertRaises(ValidationError):
            self.profile.diet = "not a list"
            self.profile.save()
    
    def test_preferred_days_validation(self):
        """Test that all preferred days fields must be valid lists of days."""
        # Valid cases
        self.profile.preferredLongRunDays = ["saturday", "sunday"]
        self.profile.preferredWorkoutDays = ["tuesday", "thursday"]
        self.profile.preferredRestDays = ["monday"]
        self.profile.save()
        
        # Invalid cases
        with self.assertRaises(ValidationError):
            self.profile.preferredLongRunDays = "not a list"
            self.profile.save()
                
        # Reset preferredLongRunDays
        self.profile.preferredLongRunDays = ["tuesday", "thursday"]
        self.profile.save()
        
        with self.assertRaises(ValidationError):
            self.profile.preferredRestDays = [1, 2, 3]
            self.profile.save()
    
    def test_past_problems_validation(self):
        """Test that pastProblems must be a valid list of strings."""
        # Valid case
        self.profile.pastProblems = ["knee_pain", "shin_splints"]
        self.profile.save()

class ProfileModelTestCase(TestCase):
    # ... existing tests ...
    
    @patch('api.utils.mixpanel_service.MixpanelService.track')
    def test_onboarding_completed_tracking(self, mock_track):
        """Test that Onboarding Completed event is tracked when is_onboarding_complete becomes true."""
        # Create a user with is_onboarding_complete=False
        user = UserFactory()
        user.profile.is_onboarding_complete = False
        user.profile.save()
        
        # Reset the mock to clear any initial calls
        mock_track.reset_mock()
        
        # Update to complete onboarding
        user.profile.is_onboarding_complete = True
        user.profile.save()
        
        # Verify Mixpanel tracking was called with correct parameters
        mock_track.assert_called_once()
        call_args = mock_track.call_args[1]
        
        # Check event name is correct
        self.assertEqual(call_args['event_name'], 'Onboarding Completed')
        
        # Check user ID is included
        self.assertEqual(call_args['distinct_id'], str(user.id))
        
        # Make sure it's not tracked on subsequent saves
        mock_track.reset_mock()
        user.profile.save()
        mock_track.assert_not_called()
        
        # Make sure it's not tracked when already true
        mock_track.reset_mock()
        user = UserFactory()
        user.profile.is_onboarding_complete = True
        user.profile.save()
        mock_track.reset_mock()
        user.profile.save()
        mock_track.assert_not_called()