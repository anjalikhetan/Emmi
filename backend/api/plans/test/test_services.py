"""
Tests for services in the plans app.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase

from api.plans.services import TrainingPlanService
from api.users.test.factories import UserFactory
from api.plans.models import Plan


class TrainingPlanServiceTest(TestCase):
    """
    Tests for the TrainingPlanService.
    """
    
    def test_send_plan_notification_with_valid_phone_number(self):
        """Test that send_plan_notification sends an SMS for a valid phone number."""
        with patch('api.users.services.TwilioMessagingService.send_sms') as mock_send:
            result = TrainingPlanService.send_plan_notification(
                "+12025550109",
                "Your training plan 'Test Plan' is now ready! Log in to view it.",
                "PlanId"
            )
        
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        self.assertEqual(args[0], "+12025550109")
        self.assertEqual(args[1], "Your training plan 'Test Plan' is now ready! Log in to view it.")
        self.assertTrue(result)
    
    def test_send_plan_notification_with_no_phone_number(self):
        """Test that send_plan_notification handles missing phone numbers."""
        with patch('api.users.services.TwilioMessagingService.send_sms') as mock_send:
            result = TrainingPlanService.send_plan_notification(
                None, 
                "Test Plan",
                "PlanId"
            )
        
        mock_send.assert_not_called()
        self.assertFalse(result)
    
    def test_send_plan_notification_handles_errors(self):
        """Test that send_plan_notification handles errors correctly."""
        with patch('api.users.services.TwilioMessagingService.send_sms') as mock_send:
            mock_send.side_effect = Exception("Test error")
            result = TrainingPlanService.send_plan_notification(
                "+12025550109", 
                "Test Plan",
                "PlanId"
            )
        
        self.assertFalse(result)

    @patch('api.utils.mixpanel_service.MixpanelService.track')
    @patch('api.plans.services.TrainingPlanService.run_prompt_one_shot')
    @patch('api.plans.services.parse_yaml_response_content')
    def test_training_plan_generated_tracking(self, mock_parse, mock_run_prompt_one_shot, mock_track):
        """Test that Training Plan Generated event is tracked when a plan is successfully generated."""

        # Create a user with a complete onboarding profile
        user = UserFactory(first_name="Alice")
        profile = user.profile
        profile.phone_number = "+12025550109"
        profile.is_onboarding_complete = True
        profile.save()

        # Create a plan for the user
        plan = Plan.objects.create(user=user)

        # Return any content for the prompt, since we're mocking the parser
        mock_run_prompt_one_shot.return_value.content = "mocked-content-does-not-matter"

        # Mock the parsed YAML output directly to bypass LLM fallback
        mock_parse.return_value = {
            "reasoning": "Build aerobic base.",
            "goal": "Half marathon",
            "sms_message": "Your plan is ready!",
            "weeks": [
                {
                    "goal": "Base building",
                    "dates": [
                        {
                            "date": "2025-03-25",
                            "workouts": [
                                {
                                    "type": "Easy Run",
                                    "summary": "Easy run for recovery",
                                    "notes": "Take it easy.",
                                    "duration": 30,
                                    "distance": 3,
                                    "focus": None,
                                    "activity": None,
                                    "steps": [
                                        {"name": "Warm-up", "description": "10 min walk"}
                                    ],
                                    "before_tips": ["Do ankle rolls"],
                                    "after_tips": ["Stretch calves"],
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        # Reset the mock to ignore any previous calls (e.g., onboarding)
        mock_track.reset_mock()

        # Run the service logic
        TrainingPlanService().generate_training_plan(plan)

        # Assert Mixpanel tracking for the plan generation happened exactly once
        mock_track.assert_called_once_with(
            distinct_id=str(user.id),
            event_name='Training Plan Generated',
            properties={'plan_id': str(plan.id)}
        )
