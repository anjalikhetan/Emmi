import random
import logging
import string
from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from api.utils.mixpanel_service import MixpanelService

from .permissions import IsUserOrReadOnly
from .serializers import CreateUserSerializer
from .serializers import UserSerializer
from .services import TwilioMessagingService

from .models import User, Profile
from api.users.models import PhoneVerification
from api.users.serializers import PhoneNumberSerializer
from api.users.throttling import PhoneNumberRateThrottle
from api.users.serializers import VerifyCodeSerializer
from rest_framework.authtoken.models import Token

class UserViewSet(mixins.RetrieveModelMixin,
                mixins.UpdateModelMixin,
                mixins.CreateModelMixin,
                viewsets.GenericViewSet):
    """
    User view set
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsUserOrReadOnly,)

    def get_serializer_class(self):
        """
        Return the serializer class based on the action.
        """
        if self.action == "create":
            return CreateUserSerializer
        return self.serializer_class

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]

    @action(detail=False)
    def me(self, request):
        serializer = self.serializer_class(
            request.user, context={"request": request}
        )
        return Response(status=status.HTTP_200_OK, data=serializer.data)

class VerificationCodeView(APIView):
    """
    API endpoint for sending verification codes to phone numbers.
    """
    permission_classes = [AllowAny]
    throttle_classes = [PhoneNumberRateThrottle]
    serializer_class = PhoneNumberSerializer
    
    def post(self, request, *args, **kwargs):
        """
        Send a verification code to the provided phone number.
        
        Uses either:
        1. Twilio Verify API if ENABLE_TWILIO_VERIFY is True and not a test number
        2. The existing verification system otherwise
        
        Returns:
            HTTP 200 OK with success message if code sent successfully
            HTTP 400 Bad Request with error details if validation fails
            HTTP 500 Internal Server Error if Twilio API call fails
        """
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid phone number."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        phone_number = serializer.validated_data['phone_number']
        
        # Initialize Twilio service
        try:
            twilio_service = TwilioMessagingService()
        except ValueError as e:
            logging.error(f"Twilio configuration error: {str(e)}")
            return Response(
                {"error": "Server configuration error. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Determine which verification method to use
        use_twilio_verify = twilio_service.should_use_twilio_verify(phone_number)
        
        if use_twilio_verify:
            # Use Twilio Verify API
            try:
                twilio_service.send_verification_code(str(phone_number))
            except Exception as e:
                logging.error(f"Twilio Verify API error: {str(e)}")
                return Response(
                    {"error": "Failed to send verification code. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # Use existing verification system
            # Delete any existing verification codes for this phone number
            PhoneVerification.objects.filter(phone_number=phone_number).delete()
            
            # Generate a random 6-digit verification code
            verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Save the new verification code
            try:
                PhoneVerification.objects.create(
                    phone_number=phone_number,
                    verification_code=verification_code
                )
            except Exception as e:
                logging.error(f"Failed to save verification code: {str(e)}")
                return Response(
                    {"error": "Failed to generate verification code."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Send the verification code via Twilio SMS
            try:
                message = f"Your verification code is: {verification_code}"
                twilio_service.send_sms(str(phone_number), message)
            except Exception as e:
                logging.error(f"SMS sending error: {str(e)}")
                return Response(
                    {"error": "Failed to send verification code. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Track Phone Number Entered event
        try:
            # Get user from request if authenticated
            user_id = str(request.user.id) if request.user.is_authenticated else None
            
            # For privacy, only include last 4 digits of phone number
            phone_str = str(phone_number)
            last_four_digits = phone_str[-4:] if len(phone_str) >= 4 else "****"
            
            # Track the event
            mixpanel_service = MixpanelService()
            mixpanel_service.track(
                distinct_id=user_id,
                event_name="Phone Number Entered",
                properties={
                    "phone_number_last_4": last_four_digits,
                    "verification_method": "twilio_verify" if use_twilio_verify else "legacy"
                },
                request=request
            )
        except Exception as e:
            # Log error but continue with normal flow
            logging.error(f"Error tracking Phone Number Entered event: {str(e)}")
        
        return Response(
            {"message": "Verification code sent successfully."},
            status=status.HTTP_200_OK
        )

class VerifyCodeView(APIView):
    """
    API endpoint for verifying verification codes sent to phone numbers.
    If verification is successful, performs user authentication:
    - If a user exists with the phone number, returns their auth token
    - If no user exists, creates a new user and returns their auth token
    """
    permission_classes = [AllowAny]
    serializer_class = VerifyCodeSerializer
    
    def post(self, request, *args, **kwargs):
        """
        Verify a verification code sent to a phone number.
        
        Uses either:
        1. Twilio Verify API if ENABLE_TWILIO_VERIFY is True and not a test number
        2. The existing verification system otherwise
        
        Returns:
            HTTP 200 OK with success message and token if code is valid
            HTTP 400 Bad Request with error details if validation fails
            HTTP 400 Bad Request with error message if code is invalid or expired
            HTTP 500 Internal Server Error if user creation fails
        """
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid input data."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        phone_number = serializer.validated_data['phone_number']
        verification_code = serializer.validated_data['verification_code']
        
        # Initialize Twilio service
        try:
            twilio_service = TwilioMessagingService()
        except ValueError as e:
            logging.error(f"Twilio configuration error: {str(e)}")
            return Response(
                {"error": "Server configuration error. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Determine which verification method to use
        use_twilio_verify = twilio_service.should_use_twilio_verify(phone_number)
        
        # Verify the code
        code_is_valid = False
        
        if use_twilio_verify:
            # Use Twilio Verify API
            try:
                code_is_valid = twilio_service.check_verification_code(
                    str(phone_number), 
                    verification_code
                )
                
                if not code_is_valid:
                    return Response(
                        {"error": "Invalid verification code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                logging.error(f"Twilio Verify API error: {str(e)}")
                return Response(
                    {"error": "Failed to verify code. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # Use existing verification system
            # Check if a matching verification code exists
            try:
                verification = PhoneVerification.objects.get(
                    phone_number=phone_number,
                    verification_code=verification_code
                )
            except PhoneVerification.DoesNotExist:
                return Response(
                    {"error": "Invalid verification code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if the code has expired
            expiry_time = verification.created_at + timedelta(
                minutes=settings.VERIFICATION_CODE_EXPIRY_MINUTES
            )
            
            if timezone.now() > expiry_time:
                # Delete the expired code
                verification.delete()
                return Response(
                    {"error": "Code has expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Code is valid and not expired, delete it
            verification.delete()
            code_is_valid = True
        
        # Authentication logic starts here
        try:
            # Look for a profile with the verified phone number
            profile = Profile.objects.filter(phone_number=phone_number).first()
            
            if profile:
                # User exists, get or create their token
                token, _ = Token.objects.get_or_create(user=profile.user)
                user = profile.user
            else:
                # User doesn't exist, create a new user with a default email and random password
                with transaction.atomic():
                    # Generate a unique email based on the phone number
                    email = f"{str(phone_number).replace('+', '')}@placeholder.com"
                    
                    # Generate a random password
                    password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(12))
                    
                    # Create the user
                    user = User.objects.create_user(
                        email=email,
                        password=password,
                        username=email,
                    )
                    
                    # Update the user's profile with the phone number
                    # (Profile is created automatically by signal, we just need to update it)
                    user.profile.phone_number = phone_number
                    user.profile.save()
                    
                    # Get token for the new user
                    token, _ = Token.objects.get_or_create(user=user)
            
            # update is_verified field to True
            user.is_verified = True
            user.save()
            
            # Track Phone Verification Completed event
            try:
                mixpanel_service = MixpanelService()
                mixpanel_service.track(
                    distinct_id=str(user.id),
                    event_name="Phone Verification Completed",
                    properties={
                        "verification_method": "twilio_verify" if use_twilio_verify else "legacy"
                    },
                    request=request
                )
            except Exception as e:
                # Log error but continue with normal flow
                logging.error(f"Error tracking Phone Verification Completed event: {str(e)}")
            
            # Return success response with the token
            return Response(
                {
                    "message": "Code verified successfully",
                    "token": token.key
                },
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            logging.error(f"Authentication error: {str(e)}")
            return Response(
                {"error": "An error occurred during authentication."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )