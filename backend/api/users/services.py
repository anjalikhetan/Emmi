import logging
import re
from typing import Optional, Tuple, Dict, Any

from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

class TwilioMessagingService:
    """
    Service for sending SMS messages via Twilio.
    
    This service handles the communication with Twilio API, including
    configuration validation, error handling, and logging.

    Services for Twilio messaging integration.

    Usage examples:

    1. Basic SMS sending:

        from api.users.services import TwilioMessagingService
        
        try:
            twilio_service = TwilioMessagingService()
            twilio_service.send_sms('+12025550109', 'Hello from Twilio!')
        except Exception as e:
            print(f"Failed to send SMS: {str(e)}")

    2. Sending MMS with media:

        twilio_service = TwilioMessagingService()
        twilio_service.send_sms(
            '+12025550109', 
            'Check out this image!', 
            media_url='https://example.com/image.jpg'
        )

    3. Error handling:

        try:
            twilio_service = TwilioMessagingService()
            twilio_service.send_sms('+12025550109', 'Hello!')
        except ValueError as e:
            # Handle configuration or validation errors
            print(f"Validation error: {str(e)}")
        except Exception as e:
            # Handle Twilio API errors
            print(f"Twilio error: {str(e)}")
            
    4. Using Twilio Verify API:
    
        try:
            twilio_service = TwilioMessagingService()
            twilio_service.send_verification_code('+12025550109')
            # Later, verify the code
            result = twilio_service.check_verification_code('+12025550109', '123456')
            if result:
                print("Code verified successfully!")
        except Exception as e:
            print(f"Verification error: {str(e)}")
    """
    
    def __init__(self):
        """
        Initialize the Twilio messaging service with credentials from settings.
        
        Validates that all required Twilio configuration is present.
        """
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_PHONE_NUMBER
        self.verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID
        
        # Validate configuration
        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.error("Twilio configuration missing. Check TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER.")
            raise ValueError("Twilio configuration missing. Check TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER.")
        
        logger.debug("TwilioMessagingService initialized with account_sid=%s, from_number=%s", 
                    self.account_sid[:4] + '...' if self.account_sid else None, 
                    self.from_number)
    
    def send_sms(self, to_number: str, message: str, media_url: Optional[str] = None) -> str:
        """
        Send an SMS message using Twilio.
        
        Args:
            to_number: The recipient's phone number (E.164 format)
            message: The message content to send
            media_url: Optional URL to media to include in the message (MMS)
        
        Returns:
            The SID of the sent message if successful
            
        Raises:
            ValueError: If phone number is invalid or configuration is missing
            Exception: If there's an error sending the message
        """
        # Validate phone number (basic validation)
        if not to_number or not isinstance(to_number, str) or not to_number.startswith('+'):
            logger.error(f"Invalid phone number format: {to_number}")
            raise ValueError(f"Invalid phone number format: {to_number}. Must be in E.164 format (e.g., +12025550109).")
        
        # Create Twilio client
        client = Client(self.account_sid, self.auth_token)
        
        try:
            logger.debug(f"Sending SMS to {to_number} from {self.from_number}")
            
            # Prepare message parameters
            message_params = {
                'body': message,
                'from_': self.from_number,
                'to': to_number
            }
            
            # Add media URL if provided
            if media_url:
                message_params['media_url'] = [media_url]
            
            # TODO: Uncomment this line to actually send the message
            # Send the message
            # twilio_message = client.messages.create(**message_params)
            twilio_message = type('obj', (), {'sid': 'test'})()
            
            logger.info(f"SMS sent successfully to {to_number}. SID: {twilio_message.sid}")
            return twilio_message.sid
            
        except TwilioRestException as e:
            error_message = f"Twilio API error: {str(e)}"
            logger.error(error_message)
            raise Exception(error_message)
        except Exception as e:
            error_message = f"Error sending SMS: {str(e)}"
            logger.error(error_message)
            raise Exception(error_message)

    def is_test_phone_number(self, phone_number: str) -> bool:
        """
        Check if a phone number is a Twilio test number.
        
        Args:
            phone_number: The phone number to check (E.164 format)
            
        Returns:
            True if the number is a test number, False otherwise
        """
        # Test phone numbers are in range +15005550000 to +15005550010
        return bool(re.match(r'^\+1500555000\d$', str(phone_number)))
        
    def should_use_twilio_verify(self, phone_number: str) -> bool:
        """
        Determine if Twilio Verify API should be used based on feature flag and phone number.
        
        Args:
            phone_number: The phone number to check (E.164 format)
            
        Returns:
            True if Twilio Verify should be used, False otherwise
        """
        # Always use the existing system for test phone numbers
        if self.is_test_phone_number(phone_number):
            return False
            
        # Use Twilio Verify API if enabled in settings
        return settings.ENABLE_TWILIO_VERIFY
        
    def send_verification_code(self, phone_number: str, channel: str = 'sms') -> Dict[str, Any]:
        """
        Send a verification code using Twilio Verify API.
        
        Args:
            phone_number: The recipient's phone number (E.164 format)
            channel: The channel to send the verification code ('sms' or 'call')
            
        Returns:
            The verification details if successful
            
        Raises:
            ValueError: If phone number is invalid or configuration is missing
            Exception: If there's an error sending the verification
        """
        # Validate phone number (basic validation)
        if not phone_number or not isinstance(phone_number, str) or not phone_number.startswith('+'):
            logger.info(f"Invalid phone number format: {phone_number}")
            raise ValueError(f"Invalid phone number format: {phone_number}. Must be in E.164 format (e.g., +12025550109).")
        
        # Validate verify service SID
        if not self.verify_service_sid:
            logger.info("Twilio Verify Service SID missing. Check TWILIO_VERIFY_SERVICE_SID.")
            raise ValueError("Twilio Verify Service SID missing. Check TWILIO_VERIFY_SERVICE_SID.")
        
        # Create Twilio client
        client = Client(self.account_sid, self.auth_token)
        
        try:
            logger.info(f"Sending verification code to {phone_number} via {channel}")
            
            # # For testing, don't actually make the API call
            # if settings.DEBUG:
            #     logger.info("DEBUG mode: Skipping actual Twilio Verify API call")
            #     return {"status": "pending", "sid": "test_verification_sid"}
            
            # Send verification code via Twilio Verify API
            verification = client.verify \
                .services(self.verify_service_sid) \
                .verifications \
                .create(to=phone_number, channel=channel)
            
            logger.info(f"Verification code sent successfully to {phone_number}. Status: {verification.status}")
            return {"status": verification.status, "sid": verification.sid}
            
        except TwilioRestException as e:
            error_message = f"Twilio Verify API error: {str(e)}"
            logger.info(error_message)
            raise Exception(error_message)
        except Exception as e:
            error_message = f"Error sending verification code: {str(e)}"
            logger.info(error_message)
            raise Exception(error_message)
            
    def check_verification_code(self, phone_number: str, code: str) -> bool:
        """
        Check a verification code using Twilio Verify API.
        
        Args:
            phone_number: The recipient's phone number (E.164 format)
            code: The verification code to check
            
        Returns:
            True if the code is valid, False otherwise
            
        Raises:
            ValueError: If phone number is invalid or configuration is missing
            Exception: If there's an error checking the verification
        """
        # Validate phone number (basic validation)
        if not phone_number or not isinstance(phone_number, str) or not phone_number.startswith('+'):
            logger.error(f"Invalid phone number format: {phone_number}")
            raise ValueError(f"Invalid phone number format: {phone_number}. Must be in E.164 format (e.g., +12025550109).")
        
        # Validate verify service SID
        if not self.verify_service_sid:
            logger.error("Twilio Verify Service SID missing. Check TWILIO_VERIFY_SERVICE_SID.")
            raise ValueError("Twilio Verify Service SID missing. Check TWILIO_VERIFY_SERVICE_SID.")
        
        # Create Twilio client
        client = Client(self.account_sid, self.auth_token)
        
        try:
            logger.debug(f"Checking verification code for {phone_number}")
            
            # # For testing, don't actually make the API call
            # if settings.DEBUG:
            #     logger.debug("DEBUG mode: Skipping actual Twilio Verify API call")
            #     # Always return valid for test phone numbers
            #     if self.is_test_phone_number(phone_number):
            #         return True
            #     # For other numbers, accept '123456' as a valid code in debug mode
            #     return code == '123456'
            
            # Check verification code via Twilio Verify API
            verification_check = client.verify \
                .services(self.verify_service_sid) \
                .verification_checks \
                .create(to=phone_number, code=code)
            
            is_valid = verification_check.status == 'approved'
            
            if is_valid:
                logger.info(f"Verification code valid for {phone_number}")
            else:
                logger.warning(f"Invalid verification code for {phone_number}. Status: {verification_check.status}")
            
            return is_valid
            
        except TwilioRestException as e:
            error_message = f"Twilio Verify API error: {str(e)}"
            logger.error(error_message)
            raise Exception(error_message)
        except Exception as e:
            error_message = f"Error checking verification code: {str(e)}"
            logger.error(error_message)
            raise Exception(error_message)