from rest_framework import serializers
from api.plans.models import Plan, Workout


class PlanSerializer(serializers.ModelSerializer):
    """Serializer for the Plan model."""
    
    class Meta:
        model = Plan
        fields = '__all__'
        

class WorkoutSerializer(serializers.ModelSerializer):
    """Serializer for the Workout model."""
    
    class Meta:
        model = Workout
        fields = '__all__'
        read_only_fields = ['workout_info', 'date', 'plan', 'id', 'created_at']
    
    def validate_completion_status(self, value):
        """Validate that completion_status is one of the allowed values."""
        allowed_values = [choice[0] for choice in Workout.CompletionStatus.choices]
        if value not in allowed_values:
            raise serializers.ValidationError(
                f"completion_status must be one of {allowed_values}"
            )
        return value
    
    def validate_difficulty(self, value):
        """Validate that difficulty is between 1 and 10."""
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("difficulty must be between 1 and 10")
        return value