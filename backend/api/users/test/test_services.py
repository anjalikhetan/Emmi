"""
Tests for services in the users app.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.conf import settings
import logging

from api.users.services import TwilioMessagingService

# TODO: Uncomment when twilio is integrated
# class TwilioMessagingServiceTest(TestCase):
#     """
#     Tests for the TwilioMessagingService.
#     """
    
#     def setUp(self):
#         """Set up test environment."""
#         # Store original settings values to restore them after tests
#         self.original_account_sid = settings.TWILIO_ACCOUNT_SID
#         self.original_auth_token = settings.TWILIO_AUTH_TOKEN
#         self.original_phone_number = settings.TWILIO_PHONE_NUMBER
        
#         # Set valid test values
#         settings.TWILIO_ACCOUNT_SID = 'test_account_sid'
#         settings.TWILIO_AUTH_TOKEN = 'test_auth_token'
#         settings.TWILIO_PHONE_NUMBER = '+12025550000'
        
#     def tearDown(self):
#         """Tear down test environment."""
#         # Restore original settings
#         settings.TWILIO_ACCOUNT_SID = self.original_account_sid
#         settings.TWILIO_AUTH_TOKEN = self.original_auth_token
#         settings.TWILIO_PHONE_NUMBER = self.original_phone_number
    
#     def test_initialization_with_valid_config(self):
#         """Test that the service initializes correctly with valid configuration."""
#         service = TwilioMessagingService()
#         self.assertEqual(service.account_sid, 'test_account_sid')
#         self.assertEqual(service.auth_token, 'test_auth_token')
#         self.assertEqual(service.from_number, '+12025550000')
    
#     def test_initialization_with_missing_config(self):
#         """Test that the service raises an error when configuration is missing."""
#         # Set missing configuration
#         settings.TWILIO_ACCOUNT_SID = ''
        
#         # Assert that initialization raises an error
#         with self.assertRaises(ValueError) as context:
#             TwilioMessagingService()
        
#         self.assertIn('Twilio configuration missing', str(context.exception))
    
#     @patch('api.users.services.Client')
#     def test_send_sms_success(self, mock_client_class):
#         """Test that send_sms successfully sends a message."""
#         # Set up mock
#         mock_client = MagicMock()
#         mock_client_class.return_value = mock_client
#         mock_message = MagicMock()
#         mock_message.sid = 'test_message_sid'
#         mock_client.messages.create.return_value = mock_message
        
#         # Call the service
#         service = TwilioMessagingService()
#         result = service.send_sms('+12025550109', 'Test message')
        
#         # Assert that the correct methods were called
#         mock_client_class.assert_called_once_with('test_account_sid', 'test_auth_token')
#         mock_client.messages.create.assert_called_once_with(
#             body='Test message',
#             from_='+12025550000',
#             to='+12025550109'
#         )
        
#         # Assert that the result is correct
#         self.assertEqual(result, 'test_message_sid')
    
#     @patch('api.users.services.Client')
#     def test_send_sms_with_media_url(self, mock_client_class):
#         """Test that send_sms successfully sends a message with media."""
#         # Set up mock
#         mock_client = MagicMock()
#         mock_client_class.return_value = mock_client
#         mock_message = MagicMock()
#         mock_message.sid = 'test_message_sid'
#         mock_client.messages.create.return_value = mock_message
        
#         # Call the service
#         service = TwilioMessagingService()
#         result = service.send_sms(
#             '+12025550109', 
#             'Test message', 
#             media_url='https://example.com/image.jpg'
#         )
        
#         # Assert that the correct methods were called
#         mock_client.messages.create.assert_called_once_with(
#             body='Test message',
#             from_='+12025550000',
#             to='+12025550109',
#             media_url=['https://example.com/image.jpg']
#         )
        
#         # Assert that the result is correct
#         self.assertEqual(result, 'test_message_sid')
    
#     def test_send_sms_invalid_phone_number(self):
#         """Test that send_sms raises an error for invalid phone numbers."""
#         service = TwilioMessagingService()
        
#         invalid_numbers = [
#             None,
#             '',
#             '1234567890',  # Missing + prefix
#             123456789,  # Not a string
#         ]
        
#         for number in invalid_numbers:
#             with self.assertRaises(ValueError) as context:
#                 service.send_sms(number, 'Test message')
            
#             self.assertIn('Invalid phone number format', str(context.exception))
    
#     @patch('api.users.services.Client')
#     def test_send_sms_twilio_error(self, mock_client_class):
#         """Test that send_sms handles Twilio API errors correctly."""
#         from twilio.base.exceptions import TwilioRestException
#         mock_client = MagicMock()
#         mock_client_class.return_value = mock_client
#         mock_client.messages.create.side_effect = TwilioRestException(
#             uri='test_uri', msg='Test Twilio error', code=123, status=400
#         )
        
#         # Disable logging
#         logging.disable(logging.CRITICAL)
        
#         service = TwilioMessagingService()
#         with self.assertRaises(Exception) as context:
#             service.send_sms('+12025550109', 'Test message')

#         logging.disable(logging.NOTSET)  # Re-enable logging
        
#         self.assertIn('Twilio API error', str(context.exception))
    
#     @patch('api.users.services.Client')
#     def test_send_sms_general_error(self, mock_client_class):
#         """Test that send_sms handles general errors correctly."""
#         # Set up mock to raise a general exception
#         mock_client = MagicMock()
#         mock_client_class.return_value = mock_client
#         mock_client.messages.create.side_effect = Exception('Test general error')
        
#         # Call the service and check for the expected exception
#         service = TwilioMessagingService()
#         with self.assertRaises(Exception) as context:
#             service.send_sms('+12025550109', 'Test message')
        
#         self.assertIn('Error sending SMS', str(context.exception))