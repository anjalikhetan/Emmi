import uuid
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient, force_authenticate
from datetime import date, timedelta
from unittest import mock, TestCase
import json

from api.plans.models import Plan, Workout
from api.plans.test.factories import PlanFactory, WorkoutFactory
from api.users.test.factories import UserFactory


class TrainingPlanGenerateViewTests(APITestCase):
    """
    Test cases for the TrainingPlanGenerateView API endpoint.
    """
    
    def setUp(self):
        """Set up test data and authenticate the user."""
        self.user = UserFactory()
        self.user.profile.is_onboarding_complete = True
        self.user.profile.save()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('generate-plan')
    
    @patch('api.plans.services.TrainingPlanThreadManager.generate_training_plan_async')
    def test_generate_plan_success(self, mock_generate):
        """Test successful training plan generation."""
        # Arrange
        mock_generate.return_value = None  # Function returns None
        
        # Act
        response = self.client.post(self.url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['status'], 'in progress')
        self.assertEqual(response.data['message'], 'Training plan generation started')
        
        # Verify the mock was called with the correct user
        mock_generate.assert_called_once_with(Plan.objects.get(user=self.user))
        
        # Verify a plan was created in the database
        self.assertTrue(Plan.objects.filter(user=self.user).exists())
    
    def test_generate_plan_unauthenticated(self):
        """Test that unauthenticated users cannot generate a plan."""
        # Arrange
        self.client.force_authenticate(user=None)
        
        # Act
        response = self.client.post(self.url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    @patch('api.plans.services.TrainingPlanThreadManager.generate_training_plan_async')
    def test_generate_plan_incomplete_profile(self, mock_generate):
        """Test that users with incomplete profiles get a 400 error."""
        # Arrange
        user = UserFactory(profile=None)
        self.client.force_authenticate(user=user)
        
        # Act
        response = self.client.post(self.url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'User profile is incomplete or missing')
        
        # Verify the mock was NOT called
        mock_generate.assert_not_called()
    
    @patch('api.plans.services.TrainingPlanThreadManager.generate_training_plan_async')
    def test_generate_plan_already_in_progress(self, mock_generate):
        """Test that users cannot generate a new plan when one is already in progress."""
        # Arrange
        # Create a plan that is in progress (no completion date or error)
        PlanFactory(user=self.user, generation_completed_at=None, generation_error=None)
        
        # Act
        response = self.client.post(self.url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['error'], 
            'A training plan is already being generated for this user'
        )
        
        # Verify the mock was NOT called
        mock_generate.assert_not_called()
    
    @patch('api.plans.services.TrainingPlanThreadManager.generate_training_plan_async')
    def test_generate_plan_server_error(self, mock_generate):
        """Test server error handling when an unexpected exception occurs."""
        # Arrange
        mock_generate.side_effect = Exception("Unexpected error")
        
        # Act
        response = self.client.post(self.url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error'], 'An unexpected error occurred')
        
        # Verify a plan was created but not started
        plan = Plan.objects.filter(user=self.user).first()
        self.assertIsNotNone(plan)
        
        # Verify the mock was called
        mock_generate.assert_called_once_with(plan)

class PlanDetailViewTests(APITestCase):
    """Test cases for the Plan Detail API endpoint."""
    
    def setUp(self):
        """Set up test data and authenticate the user."""
        self.user = UserFactory()
        self.plan = PlanFactory(user=self.user)
        self.client.force_authenticate(user=self.user)
        self.url = reverse('plan-detail', kwargs={'plan_id': self.plan.id})
    
    def test_get_plan_success(self):
        """Test successfully retrieving a plan."""
        # Act
        response = self.client.get(self.url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(self.plan.id))
        self.assertEqual(response.data['plan_info'], self.plan.plan_info)
    
    def test_get_plan_unauthenticated(self):
        """Test that unauthenticated users cannot access a plan."""
        # Arrange
        self.client.force_authenticate(user=None)
        
        # Act
        response = self.client.get(self.url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_plan_wrong_user(self):
        """Test that users cannot access plans that don't belong to them."""
        # Arrange
        other_user = UserFactory()
        self.client.force_authenticate(user=other_user)
        
        # Act
        response = self.client.get(self.url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_nonexistent_plan(self):
        """Test that requesting a non-existent plan returns 404."""
        # Arrange
        nonexistent_id = uuid.uuid4()
        url = reverse('plan-detail', kwargs={'plan_id': nonexistent_id})
        
        # Act
        response = self.client.get(url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class WorkoutListViewTests(APITestCase):
    """Test cases for the Workout List API endpoint."""
    
    def setUp(self):
        """Set up test data and authenticate the user."""
        self.user = UserFactory()
        self.plan = PlanFactory(user=self.user)
        self.client.force_authenticate(user=self.user)
        self.url = reverse('workout-list', kwargs={'plan_id': self.plan.id})

        # Create 60 workouts starting from a valid base date
        base_date = date(2023, 1, 1)
        self.workouts = [
            WorkoutFactory(plan=self.plan, date=base_date + timedelta(days=i))
            for i in range(60)
        ]
    
    def test_get_workouts_success(self):
        """Test successfully retrieving a list of workouts."""
        # Act
        response = self.client.get(self.url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 50)  # Default page size
        self.assertTrue(response.data['next'])  # Should have next page
        self.assertFalse(response.data['previous'])  # No previous page
    
    def test_get_workouts_with_date_range_filter(self):
        """Test filtering workouts by date."""
        # Arrange
        test_start_date = "2023-01-15"
        test_end_date = "2023-01-15"
        
        # Act
        response = self.client.get(f"{self.url}?start_date={test_start_date}&end_date={test_end_date}")
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['date'], test_start_date)
        self.assertEqual(response.data['results'][0]['date'], test_end_date)
    
    def test_get_workouts_empty_results(self):
        """Test getting workouts when none exist."""
        # Arrange
        # Create a new plan with no workouts
        empty_plan = PlanFactory(user=self.user)
        url = reverse('workout-list', kwargs={'plan_id': empty_plan.id})
        
        # Act
        response = self.client.get(url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_get_workouts_unauthenticated(self):
        """Test that unauthenticated users cannot access workouts."""
        # Arrange
        self.client.force_authenticate(user=None)
        
        # Act
        response = self.client.get(self.url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_workouts_wrong_user(self):
        """Test that users cannot access workouts for plans that don't belong to them."""
        # Arrange
        other_user = UserFactory()
        self.client.force_authenticate(user=other_user)
        
        # Act
        response = self.client.get(self.url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_workouts_nonexistent_plan(self):
        """Test that requesting workouts for a non-existent plan returns 404."""
        # Arrange
        nonexistent_id = uuid.uuid4()
        url = reverse('workout-list', kwargs={'plan_id': nonexistent_id})
        
        # Act
        response = self.client.get(url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_pagination_second_page(self):
        """Test accessing the second page of paginated results."""
        # Act
        response = self.client.get(f"{self.url}?page=2")
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # 60 total, 50 on first page
        self.assertFalse(response.data['next'])  # No next page
        self.assertTrue(response.data['previous'])  # Should have previous page

class WorkoutDetailViewTests(APITestCase):
    """Test cases for the Workout Detail API endpoint."""
    
    def setUp(self):
        """Set up test data and authenticate the user."""
        self.user = UserFactory()
        self.plan = PlanFactory(user=self.user)
        self.workout = WorkoutFactory(plan=self.plan)
        self.client.force_authenticate(user=self.user)
        self.url = reverse('workout-detail', kwargs={
            'plan_id': self.plan.id,
            'workout_id': self.workout.id
        })
    
    def test_get_workout_success(self):
        """Test successfully retrieving a workout."""
        # Act
        response = self.client.get(self.url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(self.workout.id))
        self.assertEqual(response.data['workout_info'], self.workout.workout_info)
    
    def test_get_workout_unauthenticated(self):
        """Test that unauthenticated users cannot access a workout."""
        # Arrange
        self.client.force_authenticate(user=None)
        
        # Act
        response = self.client.get(self.url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_workout_wrong_user(self):
        """Test that users cannot access workouts that don't belong to them."""
        # Arrange
        other_user = UserFactory()
        self.client.force_authenticate(user=other_user)
        
        # Act
        response = self.client.get(self.url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_nonexistent_workout(self):
        """Test that requesting a non-existent workout returns 404."""
        # Arrange
        nonexistent_id = uuid.uuid4()
        url = reverse('workout-detail', kwargs={
            'plan_id': self.plan.id,
            'workout_id': nonexistent_id
        })
        
        # Act
        response = self.client.get(url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_workout_wrong_plan(self):
        """Test accessing a workout with the wrong plan ID."""
        # Arrange
        other_plan = PlanFactory(user=self.user)
        url = reverse('workout-detail', kwargs={
            'plan_id': other_plan.id,
            'workout_id': self.workout.id
        })
        
        # Act
        response = self.client.get(url)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_workout_success(self):
        """Test successfully updating a workout with valid data."""
        # Arrange
        data = {
            "completion_status": "completed",
            "difficulty": 8,
            "additional_notes": "This was a great workout!"
        }
        
        # Act
        response = self.client.patch(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["completion_status"], "completed")
        self.assertEqual(response.data["difficulty"], 8)
        self.assertEqual(response.data["additional_notes"], "This was a great workout!")
        
        # Verify the changes were saved to the database
        updated_workout = Workout.objects.get(id=self.workout.id)
        self.assertEqual(updated_workout.completion_status, "completed")
        self.assertEqual(updated_workout.difficulty, 8)
        self.assertEqual(updated_workout.additional_notes, "This was a great workout!")

    def test_patch_workout_partial_update(self):
        """Test updating only some fields of a workout."""
        # Arrange
        data = {
            "completion_status": "modified"
        }
        
        # Act
        response = self.client.patch(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["completion_status"], "modified")
        
        # Verify other fields weren't changed
        updated_workout = Workout.objects.get(id=self.workout.id)
        self.assertEqual(updated_workout.completion_status, "modified")
        self.assertEqual(updated_workout.difficulty, self.workout.difficulty)
        self.assertEqual(updated_workout.additional_notes, self.workout.additional_notes)

    def test_patch_workout_invalid_completion_status(self):
        """Test updating a workout with an invalid completion status."""
        # Arrange
        data = {
            "completion_status": "invalid_status"
        }
        
        # Act
        response = self.client.patch(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("completion_status", response.data)

    def test_patch_workout_invalid_difficulty(self):
        """Test updating a workout with an invalid difficulty value."""
        # Arrange - Test difficulty too high
        data = {
            "difficulty": 11
        }
        
        # Act
        response = self.client.patch(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("difficulty", response.data)
        
        # Arrange - Test difficulty too low
        data = {
            "difficulty": 0
        }
        
        # Act
        response = self.client.patch(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("difficulty", response.data)

    def test_patch_workout_unauthorized(self):
        """Test that unauthorized users cannot update a workout."""
        # Arrange
        other_user = UserFactory()
        self.client.force_authenticate(user=other_user)
        data = {
            "completion_status": "completed"
        }
        
        # Act
        response = self.client.patch(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_nonexistent_workout(self):
        """Test updating a non-existent workout."""
        # Arrange
        nonexistent_id = uuid.uuid4()
        url = reverse('workout-detail', kwargs={
            'plan_id': self.plan.id,
            'workout_id': nonexistent_id
        })
        data = {
            "completion_status": "completed"
        }
        
        # Act
        response = self.client.patch(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_workout_no_data(self):
        """Test updating a workout with no data."""
        # Arrange
        data = {}
        
        # Act
        response = self.client.patch(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify nothing changed
        updated_workout = Workout.objects.get(id=self.workout.id)
        self.assertEqual(updated_workout.completion_status, self.workout.completion_status)
        self.assertEqual(updated_workout.difficulty, self.workout.difficulty)
        self.assertEqual(updated_workout.additional_notes, self.workout.additional_notes)

    def test_patch_workout_ignore_workout_info_and_date(self):
        """Test that workout_info and date fields are not updated."""
        # Arrange
        original_workout_info = self.workout.workout_info
        original_date = self.workout.date
        new_date = original_date + timedelta(days=7)
        
        data = {
            "completion_status": "completed",
            "workout_info": {"new": "data"},
            "date": new_date.isoformat()
        }
        
        # Act
        response = self.client.patch(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["completion_status"], "completed")
        
        # Verify workout_info and date weren't changed
        updated_workout = Workout.objects.get(id=self.workout.id)
        self.assertEqual(updated_workout.workout_info, original_workout_info)
        self.assertEqual(updated_workout.date, original_date)
    
    def test_put_method_not_allowed(self):
        """Test that PUT method is not allowed."""
        # Arrange
        data = {
            "completion_status": "completed",
            "difficulty": 8,
            "additional_notes": "This was a great workout!"
        }
        
        # Act
        response = self.client.put(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

class WorkoutDetailViewTestCase(TestCase):
    # ... existing tests ...
    
    def setUp(self):
        self.user = UserFactory()
        self.plan = Plan.objects.create(user=self.user)
        self.workout = Workout.objects.create(
            plan=self.plan,
            date=date.today(),
            workout_info={'type': 'Easy Run'},
            completion_status=Workout.CompletionStatus.NOT_COMPLETED
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('workout-detail', kwargs={
            'plan_id': self.plan.id,
            'workout_id': self.workout.id
        })
    
    @patch('api.utils.mixpanel_service.MixpanelService.track')
    def test_workout_tracking_completed_event(self, mock_track):
        """Test that Workout Tracking Completed event is tracked when status changes from not_completed."""
        data = {
            'completion_status': Workout.CompletionStatus.COMPLETED,
            'difficulty': 7,
            'additional_notes': 'Felt good today!'
        }
        
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify Mixpanel tracking was called with correct parameters
        mock_track.assert_called_once()
        call_args = mock_track.call_args[1]
        
        # Check event name is correct
        self.assertEqual(call_args['event_name'], 'Workout Tracking Completed')
        
        # Check all required properties are included
        self.assertEqual(call_args['distinct_id'], str(self.user.id))
        self.assertEqual(call_args['properties']['workout_id'], str(self.workout.id))
        self.assertEqual(call_args['properties']['date'], str(self.workout.date))
        self.assertEqual(call_args['properties']['difficulty'], 7)
        self.assertEqual(call_args['properties']['workout_type'], 'Easy Run')
        self.assertEqual(call_args['properties']['completion_status'], Workout.CompletionStatus.COMPLETED)
        self.assertEqual(call_args['properties']['additional_notes'], 'Felt good today!')
        
        # Test that events are not tracked for subsequent updates
        mock_track.reset_mock()
        data = {'additional_notes': 'Updated notes'}
        response = self.client.patch(self.url, data, format='json')
        mock_track.assert_not_called()
        
        # Test that events are not tracked when staying in not_completed status
        mock_track.reset_mock()
        self.workout.completion_status = Workout.CompletionStatus.NOT_COMPLETED
        self.workout.save()
        data = {'additional_notes': 'Another update'}
        response = self.client.patch(self.url, data, format='json')
        mock_track.assert_not_called()