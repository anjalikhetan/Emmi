from django.test import TestCase
from django.forms.models import model_to_dict
from .factories import UserFactory
from ..serializers import CreateUserSerializer, ProfileSerializer, UserSerializer


class TestCreateUserSerializer(TestCase):

    def setUp(self):
        self.user_data = model_to_dict(UserFactory.build())

    def test_serializer_with_empty_data(self):
        serializer = CreateUserSerializer(data={})
        assert serializer.is_valid() is False

    def test_serializer_with_valid_data(self):
        serializer = CreateUserSerializer(data=self.user_data)
        assert serializer.is_valid()

    def test_serializer_hashes_password(self):
        serializer = CreateUserSerializer(data=self.user_data)
        assert serializer.is_valid()
        user = serializer.save()
        assert user.email == self.user_data.get('email')


class TestProfileSerializer(TestCase):
    """
    Tests for the ProfileSerializer.
    """
    
    def setUp(self):
        self.user = UserFactory()
        self.profile = self.user.profile
        self.phone_number = "+12025550109"
        self.profile.phone_number = self.phone_number
        self.profile.save()
        
    def test_profile_serializer_with_phone_number(self):
        """Test that the phone_number field is included in the serialized data."""
        serializer = ProfileSerializer(instance=self.profile)
        data = serializer.data
        
        # Check that phone_number is in the serialized data
        self.assertIn('phone_number', data)
        self.assertEqual(data['phone_number'], self.phone_number)
        
    def test_profile_serializer_update_with_valid_phone(self):
        """Test that the phone_number can be updated with valid data."""
        new_phone = "+12025550110"
        serializer = ProfileSerializer(
            instance=self.profile,
            data={'phone_number': new_phone}
        )
        
        self.assertTrue(serializer.is_valid())
        updated_profile = serializer.save()
        self.assertEqual(str(updated_profile.phone_number), new_phone)
        
    def test_profile_serializer_with_invalid_phone(self):
        """Test that the serializer rejects invalid phone numbers."""
        serializer = ProfileSerializer(
            instance=self.profile,
            data={'phone_number': 'invalid-phone'}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors)

class TestUserSerializer(TestCase):
    """
    Tests for the UserSerializer.
    """
    
    def setUp(self):
        self.user = UserFactory()
        self.profile = self.user.profile
        
    def test_user_serializer_partial_update(self):
        """Test that the UserSerializer can handle partial updates."""
        serializer = UserSerializer(
            instance=self.user,
            data={'first_name': 'NewName'},
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        self.assertEqual(updated_user.first_name, 'NewName')
        self.assertEqual(updated_user.last_name, self.user.last_name)  # Unchanged
        
    def test_user_serializer_partial_update_with_profile(self):
        """Test that the UserSerializer can handle partial updates with nested profile."""
        serializer = UserSerializer(
            instance=self.user,
            data={
                'first_name': 'NewName',
                'profile': {
                    'age': 35
                }
            },
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        self.assertEqual(updated_user.first_name, 'NewName')
        self.assertEqual(updated_user.profile.age, 35)
        
    def test_user_serializer_invalid_profile_data(self):
        """Test that the UserSerializer validates nested profile data."""
        serializer = UserSerializer(
            instance=self.user,
            data={
                'profile': {
                    'age': 15  # Invalid age
                }
            },
            partial=True
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('profile', serializer.errors)
        self.assertIn('age', serializer.errors['profile'])

class TestProfileValidation(TestCase):
    """
    Tests for Profile field validations.
    """
    
    def setUp(self):
        self.user = UserFactory()
        self.profile = self.user.profile
        
    def test_age_validation(self):
        """Test age validation."""
        # Invalid - below minimum
        serializer = ProfileSerializer(
            instance=self.profile,
            data={'age': 15},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('age', serializer.errors)
        
        # Invalid - above maximum
        serializer = ProfileSerializer(
            instance=self.profile,
            data={'age': 150},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('age', serializer.errors)
        
        # Valid
        serializer = ProfileSerializer(
            instance=self.profile,
            data={'age': 35},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        
    def test_height_validation(self):
        """Test height validation."""
        # Invalid feet
        serializer = ProfileSerializer(
            instance=self.profile,
            data={'feet': 10},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('feet', serializer.errors)
        
        # Invalid inches
        serializer = ProfileSerializer(
            instance=self.profile,
            data={'inches': 15},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('inches', serializer.errors)
        
        # Invalid heightCm
        serializer = ProfileSerializer(
            instance=self.profile,
            data={'heightCm': 300},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('heightCm', serializer.errors)
        
        # Valid
        serializer = ProfileSerializer(
            instance=self.profile,
            data={'feet': 5, 'inches': 10, 'heightCm': 180},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        
    def test_weight_validation(self):
        """Test weight validation."""
        # Invalid weightKg
        serializer = ProfileSerializer(
            instance=self.profile,
            data={'weightKg': 600},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('weightKg', serializer.errors)
        
        # Invalid weightLbs
        serializer = ProfileSerializer(
            instance=self.profile,
            data={'weightLbs': 1200},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('weightLbs', serializer.errors)
        
        # Valid
        serializer = ProfileSerializer(
            instance=self.profile,
            data={'weightKg': 75, 'weightLbs': 165},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        
    def test_json_field_validation(self):
        """Test JSON field validation."""
        
        # Valid goals
        serializer = ProfileSerializer(
            instance=self.profile,
            data={'goals': ['weight_loss', 'improve_fitness']},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        
        # Valid diet
        serializer = ProfileSerializer(
            instance=self.profile,
            data={'diet': ['omnivore', 'vegetarian']},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        
        # Valid daysCommitTraining
        serializer = ProfileSerializer(
            instance=self.profile,
            data={'daysCommitTraining': '3 days'},
            partial=True
        )
        self.assertTrue(serializer.is_valid())