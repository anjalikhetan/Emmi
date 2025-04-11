import logging
import uuid
from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from rest_framework import status, generics, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from api.plans.models import Plan, Workout
from api.plans.services import TrainingPlanThreadManager
from api.plans.serializers import PlanSerializer, WorkoutSerializer
from api.users.permissions import IsPlanOwner
from api.utils.mixpanel_service import MixpanelService

logger = logging.getLogger(__name__)

class TrainingPlanGenerateView(APIView):
    """
    API endpoint to initiate the generation of a training plan.
    
    POST: Start generating a new training plan for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """
        Initiate the generation of a training plan for the authenticated user.
        
        Returns:
            Response with status 201 and plan details on success,
            or error response with appropriate status code.
        """
        user = request.user

        try:
            # Check if user profile exists and is complete
            if not hasattr(user, 'profile') or not user.profile or not user.profile.is_onboarding_complete:
                return Response(
                    {"error": "User profile is incomplete or missing"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if a plan is already being generated for this user
            if Plan.objects.filter(
                user=user, 
                generation_completed_at__isnull=True, 
                generation_error__isnull=True
            ).exists():
                return Response(
                    {"error": "A training plan is already being generated for this user"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create a new plan
            plan = Plan.objects.create(user=user)
            
            # Start async generation
            TrainingPlanThreadManager().generate_training_plan_async(plan)
            
            # Return success response
            return Response(
                {
                    "id": plan.id,
                    "status": "in progress",
                    "message": "Training plan generation started"
                },
                status=status.HTTP_201_CREATED
            )
        
        except ValidationError as e:
            logger.error(f"Validation error while creating plan for user {user.id}: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error while creating plan for user {user.id}: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PlanDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific training plan.
    
    Returns all attributes of the Plan model in the response.
    Ensures the plan belongs to the requesting user.
    """
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated, IsPlanOwner]
    
    def get_object(self):
        """Get the plan object ensuring it belongs to the user."""
        plan_id = self.kwargs.get('plan_id')
        plan = get_object_or_404(Plan, id=plan_id)
        self.check_object_permissions(self.request, plan)
        return plan

class WorkoutPagination(PageNumberPagination):
    """
    Pagination class for DealViewSet.
    
    * Sets page size to 50 items.
    * Provides pagination metadata including count, next, previous, and results.
    """
    page_size = 50

class WorkoutListView(generics.ListAPIView):
    """
    List workouts for a specific training plan.
    
    Returns all attributes of the Workout model for each item.
    Implements pagination with 50 items per page.
    Includes filter by date in YYYY-MM-DD format.
    Ensures the plan belongs to the requesting user.
    """
    serializer_class = WorkoutSerializer
    permission_classes = [IsAuthenticated, IsPlanOwner]
    pagination_class = WorkoutPagination
    
    def get_queryset(self):
        """
        Filter workouts for the specified plan.
        Also filter by a date range if start_date and end_date are provided.
        """
        plan_id = self.kwargs.get('plan_id')
        queryset = Workout.objects.filter(plan_id=plan_id)

        # Range filter: start_date and end_date
        start_date_str = self.request.query_params.get('start_date')
        end_date_str = self.request.query_params.get('end_date')

        if start_date_str and end_date_str:
            start_date = parse_date(start_date_str)
            end_date = parse_date(end_date_str)
            if start_date and end_date:
                queryset = queryset.filter(date__range=(start_date, end_date))
        elif start_date_str:
            start_date = parse_date(start_date_str)
            if start_date:
                queryset = queryset.filter(date__gte=start_date)
        elif end_date_str:
            end_date = parse_date(end_date_str)
            if end_date:
                queryset = queryset.filter(date__lte=end_date)
        return queryset
        
    def get_paginated_response(self, data):
        """Customize pagination to include 50 items per page."""
        self.pagination_class.page_size = 50
        return super().get_paginated_response(data)

class WorkoutDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a specific workout.
    
    GET: Return all attributes of the Workout model in the response.
    PATCH: Allow partial updates to completion_status, difficulty, and additional_notes.
    
    Ensures the workout's plan belongs to the requesting user.
    """
    serializer_class = WorkoutSerializer
    permission_classes = [IsAuthenticated, IsPlanOwner]
    http_method_names = ['get', 'patch', 'head', 'options']  # Only allow GET and PATCH
    
    def get_object(self):
        """
        Get the workout object ensuring its plan belongs to the user.
        """
        plan_id = self.kwargs.get('plan_id')
        workout_id = self.kwargs.get('workout_id')
        
        # The IsPlanOwner permission already checks if plan belongs to user
        workout = get_object_or_404(Workout, id=workout_id, plan_id=plan_id)
        self.check_object_permissions(self.request, workout)
        return workout
    
    def update(self, request, *args, **kwargs):
        """
        Override update to ensure partial updates and validation of input data.
        Ignores workout_info and date fields.
        """
        # Only support partial updates (PATCH)
        if not kwargs.get('partial', False):
            return Response(
                {"error": "Only PATCH method is supported for updates"},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        
        # Get the workout object
        instance = self.get_object()
        
        # Create a copy of request data to modify
        data = request.data.copy()
        
        # Remove workout_info and date fields if present
        if 'workout_info' in data:
            data.pop('workout_info')
        
        if 'date' in data:
            data.pop('date')
        
        # Store original completion status for comparison
        original_completion_status = instance.completion_status
        
        # Validate and update
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Check if completion status has changed from not_completed to something else
        updated_instance = self.get_object()  # Get the fresh instance
        new_completion_status = updated_instance.completion_status
        
        if (original_completion_status == Workout.CompletionStatus.NOT_COMPLETED and 
            new_completion_status != Workout.CompletionStatus.NOT_COMPLETED):
            try:
                # Extract workout type from workout_info
                workout_type = updated_instance.workout_info.get('type', 'Unknown') if updated_instance.workout_info else 'Unknown'
                
                # Track the workout completion event
                mixpanel_service = MixpanelService()
                mixpanel_service.track(
                    distinct_id=str(request.user.id),
                    event_name="Workout Tracking Completed",
                    properties={
                        "workout_id": str(updated_instance.id),
                        "date": str(updated_instance.date),
                        "difficulty": updated_instance.difficulty,
                        "workout_type": workout_type,
                        "completion_status": updated_instance.completion_status,
                        "additional_notes": updated_instance.additional_notes
                    },
                    request=request
                )
            except Exception as e:
                # Log error but continue with normal flow
                logging.error(f"Error tracking Workout Tracking Completed event: {str(e)}")
        
        return Response(serializer.data)