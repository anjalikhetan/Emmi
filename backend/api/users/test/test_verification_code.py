from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from django.test import TestCase, override_settings
from api.users.models import PhoneVerification
from api.users.test.factories import PhoneVerificationFactory
from django.conf import settings

class VerificationCodeViewTest(APITestCase):
    """
    Tests for the verification code API endpoint.
    """
    
    def setUp(self):
        """Set up test environment."""
        self.url = reverse('verification-code', kwargs={})
        self.valid_phone_number = "+12025550109"
        self.test_phone_number = "+15005550001"
        self.invalid_phone_number = "invalid-phone"
    
    def test_valid_phone_number_creates_verification_code(self):
        """Test that a valid phone number creates a new verification code with legacy system."""
        with patch('api.users.services.TwilioMessagingService.send_sms') as mock_send, \
            patch('api.users.services.TwilioMessagingService.should_use_twilio_verify', return_value=False):
            response = self.client.post(
                self.url,
                {"phone_number": self.valid_phone_number},
                format='json'
            )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "Verification code sent successfully."})
        
        # Assert the verification code was created
        self.assertEqual(PhoneVerification.objects.count(), 1)
        verification = PhoneVerification.objects.first()
        self.assertEqual(str(verification.phone_number), self.valid_phone_number)
        self.assertEqual(len(verification.verification_code), 6)
        self.assertTrue(verification.verification_code.isdigit())
    
    @override_settings(ENABLE_TWILIO_VERIFY=True)
    def test_valid_phone_number_uses_twilio_verify(self):
        """Test that a valid phone number uses Twilio Verify API when enabled."""
        with patch('api.users.services.TwilioMessagingService.send_verification_code') as mock_verify, \
            patch('api.users.services.TwilioMessagingService.should_use_twilio_verify', return_value=True):
            mock_verify.return_value = {"status": "pending", "sid": "test_sid"}
            response = self.client.post(
                self.url,
                {"phone_number": self.valid_phone_number},
                format='json'
            )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "Verification code sent successfully."})
        
        # Assert Twilio Verify was called
        mock_verify.assert_called_once_with(str(self.valid_phone_number))
        
        # Assert no verification code was created in database (as Twilio Verify handles it)
        self.assertEqual(PhoneVerification.objects.count(), 0)
    
    @override_settings(ENABLE_TWILIO_VERIFY=True)
    def test_test_phone_number_uses_legacy_system(self):
        """Test that test phone numbers always use the legacy system."""
        with patch('api.users.services.TwilioMessagingService.send_sms') as mock_send:
            response = self.client.post(
                self.url,
                {"phone_number": self.test_phone_number},
                format='json'
            )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert a verification code was created (legacy system)
        self.assertEqual(PhoneVerification.objects.count(), 1)
        verification = PhoneVerification.objects.first()
        self.assertEqual(str(verification.phone_number), self.test_phone_number)
    
    def test_invalid_phone_number_returns_400(self):
        """Test that an invalid phone number returns a 400 error."""
        response = self.client.post(
            self.url,
            {"phone_number": self.invalid_phone_number},
            format='json'
        )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Invalid phone number."})
        
        # Assert no verification code was created
        self.assertEqual(PhoneVerification.objects.count(), 0)
    
    def test_twilio_error_returns_500(self):
        """Test that a Twilio error returns a 500 error."""
        with patch('api.users.services.TwilioMessagingService.send_sms') as mock_send, \
            patch('api.users.services.TwilioMessagingService.should_use_twilio_verify', return_value=False):
            mock_send.side_effect = Exception("Twilio error")
            response = self.client.post(
                self.url,
                {"phone_number": self.valid_phone_number},
                format='json'
            )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {"error": "Failed to send verification code. Please try again later."})
    
    @override_settings(ENABLE_TWILIO_VERIFY=True)
    def test_twilio_verify_error_returns_500(self):
        """Test that a Twilio Verify API error returns a 500 error."""
        with patch('api.users.services.TwilioMessagingService.send_verification_code') as mock_verify, \
            patch('api.users.services.TwilioMessagingService.should_use_twilio_verify', return_value=True):
            mock_verify.side_effect = Exception("Twilio Verify error")
            response = self.client.post(
                self.url,
                {"phone_number": self.valid_phone_number},
                format='json'
            )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {"error": "Failed to send verification code. Please try again later."})
    
    def test_existing_codes_are_deleted(self):
        """Test that existing verification codes are deleted before creating a new one."""
        # Create an existing verification code
        existing_code = PhoneVerificationFactory(phone_number=self.valid_phone_number)
        
        # Send a new verification code
        with patch('api.users.services.TwilioMessagingService.send_sms'), \
            patch('api.users.services.TwilioMessagingService.should_use_twilio_verify', return_value=False):
            response = self.client.post(
                self.url,
                {"phone_number": self.valid_phone_number},
                format='json'
            )
        
        # Assert the response is correct
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert there's still only one verification code
        self.assertEqual(PhoneVerification.objects.count(), 1)
        
        # Assert the new code is different from the old one
        new_code = PhoneVerification.objects.first()
        self.assertNotEqual(new_code.verification_code, existing_code.verification_code)
    
    @patch('api.users.throttling.PhoneNumberRateThrottle.allow_request', return_value=False)
    @patch('api.users.throttling.PhoneNumberRateThrottle.wait', return_value=None)
    def test_rate_limiting(self, mock_wait, mock_allow):
        response = self.client.post(
            self.url,
            {"phone_number": self.valid_phone_number},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

class VerificationCodeViewTestCase(TestCase):
    @patch('api.users.services.TwilioMessagingService.send_verification_code', return_value={"status": "pending", "sid": "test_verification_sid"})
    @patch('api.users.services.TwilioMessagingService.send_sms', return_value="test_sms_sid")
    @patch('api.utils.mixpanel_service.MixpanelService.track')
    def test_phone_number_entered_tracking(self, mock_track, mock_send_sms, mock_send_verification_code):
        """Test that Phone Number Entered event is tracked when verification code is sent."""
        
        client = APIClient()
        url = reverse('verification-code')
        data = {'phone_number': '+12025550108'}
        
        response = client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify Twilio send_sms or send_verification_code was called
        if mock_send_verification_code.called:
            mock_send_verification_code.assert_called_once_with(str(data['phone_number']))
        else:
            mock_send_sms.assert_called_once_with(str(data['phone_number']), 'Your verification code is: 123456')
        
        # Verify Mixpanel tracking was called with correct parameters
        mock_track.assert_called_once()
        call_args = mock_track.call_args[1]
        
        # Check event name is correct
        self.assertEqual(call_args['event_name'], 'Phone Number Entered')
        
        # Check properties include last 4 digits of phone number
        self.assertEqual(call_args['properties']['phone_number_last_4'], '0108')
        
        # Verify distinct_id handling for anonymous users
        self.assertIsNone(call_args['distinct_id'])