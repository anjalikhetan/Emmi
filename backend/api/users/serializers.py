from rest_framework import serializers
from django.conf import settings

from api.users.models import User
from api.users.models import Profile
from api.plans.models import Plan


class ProfileSerializer(serializers.ModelSerializer):
    """
    User Profile serializer with field-level validation
    """
    class Meta:
        model = Profile
        exclude = ('id', 'user')
    
    def validate_age(self, value):
        """Validate age is between 18 and 120"""
        if value is not None and (value < 18 or value > 120):
            raise serializers.ValidationError("Age must be between 18 and 120.")
        return value
    
    def validate_feet(self, value):
        """Validate feet is between 1 and 8"""
        if value is not None and (value < 1 or value > 8):
            raise serializers.ValidationError("Feet must be between 1 and 8.")
        return value
    
    def validate_inches(self, value):
        """Validate inches is between 0 and 11"""
        if value is not None and (value < 0 or value > 11):
            raise serializers.ValidationError("Inches must be between 0 and 11.")
        return value
    
    def validate_heightCm(self, value):
        """Validate height in cm is between 100 and 250"""
        if value is not None and (value < 100 or value > 250):
            raise serializers.ValidationError("Height must be between 100 and 250 cm.")
        return value
    
    def validate_weightKg(self, value):
        """Validate weight in kg is between 10 and 500"""
        if value is not None and (value < 10 or value > 500):
            raise serializers.ValidationError("Weight must be between 10 and 500 kg.")
        return value
    
    def validate_weightLbs(self, value):
        """Validate weight in lbs is between 22 and 1100"""
        if value is not None and (value < 22 or value > 1100):
            raise serializers.ValidationError("Weight must be between 22 and 1100 lbs.")
        return value
    
    def validate_raceDate(self, value):
        """Validate race date is a valid date"""
        if value is not None:
            try:
                # The value should already be a date object at this point
                # Just ensure it's a valid date object
                return value
            except (ValueError, TypeError):
                raise serializers.ValidationError("Invalid date format. Use ISO format (YYYY-MM-DD).")
        return value
    
    def validate_goals(self, value):
        """Validate goals using the custom validator"""
        if value is not None:
            from api.users.validators import validate_goals_list
            try:
                validate_goals_list(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        return value
    
    def validate_extraTraining(self, value):
        """Validate extraTraining using the custom validator"""
        if value is not None:
            from api.users.validators import validate_extra_training_list
            try:
                validate_extra_training_list(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        return value
    
    def validate_diet(self, value):
        """Validate diet using the custom validator"""
        if value is not None:
            from api.users.validators import validate_diet_list
            try:
                validate_diet_list(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        return value
    
    def validate_preferredLongRunDays(self, value):
        """Validate preferredLongRunDays using the custom validator"""
        if value is not None:
            from api.users.validators import validate_days_of_week_list
            try:
                validate_days_of_week_list(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        return value
    
    def validate_preferredWorkoutDays(self, value):
        """Validate preferredWorkoutDays using the custom validator"""
        if value is not None:
            from api.users.validators import validate_days_of_week_list
            try:
                validate_days_of_week_list(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        return value
    
    def validate_preferredRestDays(self, value):
        """Validate preferredRestDays using the custom validator"""
        if value is not None:
            from api.users.validators import validate_days_of_week_list
            try:
                validate_days_of_week_list(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        return value
    
    def validate_pastProblems(self, value):
        """Validate pastProblems using the custom validator"""
        if value is not None:
            from api.users.validators import validate_past_problems_list
            try:
                validate_past_problems_list(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        return value

class UserSerializer(serializers.ModelSerializer):
    """
    User serializer with support for nested profile updates
    """
    profile = ProfileSerializer(required=False)
    current_plan = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'profile',
            'is_verified',
            'current_plan',
        )
        read_only_fields = ('id', 'email', 'is_verified', 'current_plan')
        
    def get_current_plan(self, obj):
        """
        Retrieve the most recent plan for the given user.
        """
        plan = Plan.objects.filter(user=obj).first()
        return getattr(plan, "id", None)
    
    def update(self, instance, validated_data):
        """
        Update User instance and its related Profile.
        Handle nested Profile data appropriately.
        """
        # Extract profile data if provided
        profile_data = validated_data.pop('profile', None)
        
        # Update the User instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update Profile if profile data was provided
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance

class CreateUserSerializer(serializers.ModelSerializer):
    """
    User create serializer
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'password',
            'first_name',
            'last_name',
            'email',
            'auth_token',
        )
        read_only_fields = ('auth_token',)

    def create(self, validated_data):
        """
        Create a new user with email as username.
        """
        validated_data['username'] = validated_data.get('email')
        user = User.objects.create_user(**validated_data)
        return user

class PhoneNumberSerializer(serializers.Serializer):
    """
    Serializer for phone number validation.
    """
    phone_number = serializers.CharField()
    
    def validate_phone_number(self, value):
        """
        Validate the phone number using PhoneNumberField.
        """
        from phonenumber_field.phonenumber import PhoneNumber
        from django.core.exceptions import ValidationError
        
        try:
            phone_number = PhoneNumber.from_string(value)
            if not phone_number.is_valid():
                raise serializers.ValidationError("Invalid phone number format.")
            return phone_number
        except Exception:
            raise serializers.ValidationError("Invalid phone number format.")

class VerifyCodeSerializer(serializers.Serializer):
    """
    Serializer for verification code validation.
    """
    phone_number = serializers.CharField()
    verification_code = serializers.CharField()
    
    def validate_phone_number(self, value):
        """
        Validate the phone number using PhoneNumberField.
        """
        from phonenumber_field.phonenumber import PhoneNumber
        
        try:
            phone_number = PhoneNumber.from_string(value)
            if not phone_number.is_valid():
                raise serializers.ValidationError("Invalid phone number format.")
            return phone_number
        except Exception:
            raise serializers.ValidationError("Invalid phone number format.")
    
    def validate_verification_code(self, value):
        """
        Validate that the verification code is exactly 6 digits.
        """
        import re
        if not re.match(r'^\d{6}$', value):
            raise serializers.ValidationError("Verification code must be exactly 6 digits.")
        return value