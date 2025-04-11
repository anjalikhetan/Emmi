import uuid
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from api.users.test.factories import UserFactory
from api.plans.models import Plan, Workout


class TestPlanModel(TestCase):
    """
    Tests for the Plan model.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.plan = Plan.objects.create(
            user=self.user,
            plan_info={"type": "training", "weeks": 12}
        )
    
    def test_plan_creation(self):
        """Test that a Plan instance can be created."""
        self.assertIsInstance(self.plan, Plan)
        self.assertEqual(str(self.plan.user.id), str(self.user.id))
        self.assertEqual(self.plan.plan_info["type"], "training")
        self.assertEqual(self.plan.plan_info["weeks"], 12)
    
    def test_plan_string_representation(self):
        """Test the string representation of Plan objects."""
        self.assertEqual(
            str(self.plan),
            f"Plan for {self.user.email}"
        )
    
    def test_plan_user_deletion_cascade(self):
        """Test that deleting a user cascades to delete related plans."""
        plan_id = self.plan.id
        self.user.delete()
        self.assertEqual(Plan.objects.filter(id=plan_id).count(), 0)
    
    def test_plan_without_user_raises_error(self):
        """Test that creating a Plan without a user raises an error."""
        with self.assertRaises(ValidationError):
            plan = Plan(plan_info={"type": "training"})
            plan.save()
    
    def test_plan_with_null_plan_info(self):
        """Test that a Plan can have null plan_info."""
        plan = Plan.objects.create(user=self.user, plan_info=None)
        self.assertIsNone(plan.plan_info)


class TestWorkoutModel(TestCase):
    """
    Tests for the Workout model.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.plan = Plan.objects.create(
            user=self.user,
            plan_info={"type": "training", "weeks": 12}
        )
        self.workout = Workout.objects.create(
            plan=self.plan,
            date=timezone.now().date(),
            completion_status="skipped",
            workout_info={"type": "run", "distance": "5km"}
        )
    
    def test_workout_creation(self):
        """Test that a Workout instance can be created."""
        self.assertIsInstance(self.workout, Workout)
        self.assertEqual(self.workout.plan, self.plan)
        self.assertEqual(self.workout.completion_status, "skipped")
        self.assertEqual(self.workout.workout_info["type"], "run")
        self.assertEqual(self.workout.workout_info["distance"], "5km")
    
    def test_workout_string_representation(self):
        """Test the string representation of Workout objects."""
        self.assertEqual(
            str(self.workout),
            f"Workout {self.workout.id} on {self.workout.date} for {self.user.email}"
        )
    
    def test_workout_plan_deletion_cascade(self):
        """Test that deleting a plan cascades to delete related workouts."""
        workout_id = self.workout.id
        self.plan.delete()
        self.assertEqual(Workout.objects.filter(id=workout_id).count(), 0)
    
    def test_workout_without_plan_raises_error(self):
        """Test that creating a Workout without a plan raises an error."""
        with self.assertRaises(ValidationError):
            workout = Workout(
                date=timezone.now().date(),
                workout_info={"type": "run"}
            )
            workout.save()
    
    def test_workout_without_workout_info_raises_error(self):
        """Test that creating a Workout without workout_info raises an error."""
        with self.assertRaises(ValidationError):
            workout = Workout(
                plan=self.plan,
                date=timezone.now().date()
            )
            workout.save()
    
    def test_workout_completion_toggle(self):
        """Test toggling the completion_status field."""
        self.assertEqual(self.workout.completion_status, "skipped")
        self.workout.completion_status = "completed"
        self.workout.save()
        
        # Refresh from db
        self.workout.refresh_from_db()
        self.assertEqual(self.workout.completion_status, "completed")