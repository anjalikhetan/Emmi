import datetime
from django.utils import timezone
from django.conf import settings
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from rest_framework.authtoken.models import Token
from api.users.models import PhoneVerification, User, Profile
from api.users.test.factories import PhoneVerificationFactory, UserFactory
from django.test import TestCase, override_settings


class VerifyCodeViewTest(APITestCase):
    """Tests for the verify code API endpoint."""
    
    def setUp(self):
        """Set up test environment."""
        self.url = reverse('verify-code')
        self.valid_phone_number = "+12025550109"
        self.test_phone_number = "+15005550001"
        self.valid_code = "123456"
        
        # Create a verification code for testing
        self.verification = PhoneVerificationFactory(
            phone_number=self.valid_phone_number,
            verification_code=self.valid_code
        )
        
        # Create a verification code for test phone number
        self.test_verification = PhoneVerificationFactory(
            phone_number=self.test_phone_number,
            verification_code=self.valid_code
        )
    
    def test_valid_code_returns_token(self):
        """Test that a valid code returns a token using legacy system."""
        with patch('api.users.services.TwilioMessagingService.should_use_twilio_verify', return_value=False):
            response = self.client.post(
                self.url,
                {
                    "phone_number": self.valid_phone_number,
                    "verification_code": self.valid_code
                },
                format='json'
            )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["message"], "Code verified successfully")
        
        # Assert the verification code was deleted
        with self.assertRaises(PhoneVerification.DoesNotExist):
            PhoneVerification.objects.get(
                phone_number=self.valid_phone_number,
                verification_code=self.valid_code
            )
        
        # Assert a user was created with the phone number
        user = User.objects.get(profile__phone_number=self.valid_phone_number)
        self.assertTrue(user.is_verified)
    
    @override_settings(ENABLE_TWILIO_VERIFY=True)
    def test_valid_code_using_twilio_verify(self):
        """Test that a valid code is verified using Twilio Verify API."""
        with patch('api.users.services.TwilioMessagingService.check_verification_code') as mock_check, \
             patch('api.users.services.TwilioMessagingService.should_use_twilio_verify', return_value=True):
            mock_check.return_value = True
            response = self.client.post(
                self.url,
                {
                    "phone_number": self.valid_phone_number,
                    "verification_code": self.valid_code
                },
                format='json'
            )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        
        # Assert Twilio Verify API was called
        mock_check.assert_called_once_with(str(self.valid_phone_number), self.valid_code)
        
        # Assert a user was created with the phone number
        user = User.objects.get(profile__phone_number=self.valid_phone_number)
        self.assertTrue(user.is_verified)
    
    @override_settings(ENABLE_TWILIO_VERIFY=True)
    def test_test_phone_number_uses_legacy_system(self):
        """Test that test phone numbers always use the legacy system."""
        response = self.client.post(
            self.url,
            {
                "phone_number": self.test_phone_number,
                "verification_code": self.valid_code
            },
            format='json'
        )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        
        # Assert the verification code was deleted (legacy system)
        with self.assertRaises(PhoneVerification.DoesNotExist):
            PhoneVerification.objects.get(
                phone_number=self.test_phone_number,
                verification_code=self.valid_code
            )
    
    def test_invalid_code_returns_400(self):
        """Test that an invalid code returns a 400 error."""
        with patch('api.users.services.TwilioMessagingService.should_use_twilio_verify', return_value=False):
            response = self.client.post(
                self.url,
                {
                    "phone_number": self.valid_phone_number,
                    "verification_code": "999999"  # Invalid code
                },
                format='json'
            )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Invalid verification code"})
    
    @override_settings(ENABLE_TWILIO_VERIFY=True)
    def test_invalid_code_with_twilio_verify_returns_400(self):
        """Test that an invalid code with Twilio Verify returns a 400 error."""
        with patch('api.users.services.TwilioMessagingService.check_verification_code') as mock_check, \
             patch('api.users.services.TwilioMessagingService.should_use_twilio_verify', return_value=True):
            mock_check.return_value = False
            response = self.client.post(
                self.url,
                {
                    "phone_number": self.valid_phone_number,
                    "verification_code": "999999"  # Invalid code
                },
                format='json'
            )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Invalid verification code"})
    
    def test_expired_code_returns_400(self):
        """Test that an expired code returns a 400 error."""
        # Make the code expired
        self.verification.created_at = timezone.now() - datetime.timedelta(
            minutes=settings.VERIFICATION_CODE_EXPIRY_MINUTES + 1
        )
        self.verification.save()
        
        with patch('api.users.services.TwilioMessagingService.should_use_twilio_verify', return_value=False):
            response = self.client.post(
                self.url,
                {
                    "phone_number": self.valid_phone_number,
                    "verification_code": self.valid_code
                },
                format='json'
            )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Code has expired"})
        
        # Assert the expired code was deleted
        with self.assertRaises(PhoneVerification.DoesNotExist):
            PhoneVerification.objects.get(
                phone_number=self.valid_phone_number,
                verification_code=self.valid_code
            )
    
    @override_settings(ENABLE_TWILIO_VERIFY=True)
    def test_twilio_verify_error_returns_500(self):
        """Test that a Twilio Verify API error returns a 500 error."""
        with patch('api.users.services.TwilioMessagingService.check_verification_code') as mock_check, \
             patch('api.users.services.TwilioMessagingService.should_use_twilio_verify', return_value=True):
            mock_check.side_effect = Exception("Twilio Verify error")
            response = self.client.post(
                self.url,
                {
                    "phone_number": self.valid_phone_number,
                    "verification_code": self.valid_code
                },
                format='json'
            )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {"error": "Failed to verify code. Please try again later."})
    
    def test_invalid_data_returns_400(self):
        """Test that invalid data returns a 400 error."""
        response = self.client.post(
            self.url,
            {
                "phone_number": "invalid-phone",
                "verification_code": self.valid_code
            },
            format='json'
        )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Invalid input data."})
    
    def test_existing_user_returns_token(self):
        """Test that an existing user with the phone number gets their token."""
        # Create a user with the phone number
        user = UserFactory()
        user.profile.phone_number = self.valid_phone_number
        user.profile.save()
        
        with patch('api.users.services.TwilioMessagingService.should_use_twilio_verify', return_value=False):
            response = self.client.post(
                self.url,
                {
                    "phone_number": self.valid_phone_number,
                    "verification_code": self.valid_code
                },
                format='json'
            )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        
        # Assert the user is marked as verified
        user.refresh_from_db()
        self.assertTrue(user.is_verified)

class VerifyCodeViewTestCase(TestCase):
    
    @patch('api.users.services.TwilioMessagingService.check_verification_code', return_value=True)
    @patch('api.users.services.TwilioMessagingService.should_use_twilio_verify', return_value=True)
    @patch('api.utils.mixpanel_service.MixpanelService.track')
    def test_phone_verification_completed_tracking(self, mock_track, mock_should_use_twilio_verify, mock_check_verification_code):
        """Test that Phone Verification Completed event is tracked when code is verified."""
        phone_number = '+12025550108'
        verification_code = '123456'
        
        # Create a verification code for testing
        PhoneVerification.objects.create(
            phone_number=phone_number, 
            verification_code=verification_code
        )
        
        client = APIClient()
        url = reverse('verify-code')
        data = {
            'phone_number': phone_number,
            'verification_code': verification_code
        }
        
        # Perform the request
        response = client.post(url, data, format='json')
        
        # Assert the response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

        # Verify Mixpanel tracking was called with correct parameters
        mock_track.assert_called_once()
        call_args = mock_track.call_args[1]

        # Check event name is correct
        self.assertEqual(call_args['event_name'], 'Phone Verification Completed')

        # Verify a user ID is included (newly created user)
        user = User.objects.get(profile__phone_number=phone_number)
        self.assertEqual(call_args['distinct_id'], str(user.id))