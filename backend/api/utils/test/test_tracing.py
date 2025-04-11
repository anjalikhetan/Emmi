from django.test import TestCase
from unittest.mock import patch, MagicMock
from api.utils.tracing import get_langfuse_handler
from api.users.test.factories import UserFactory
from api.plans.test.factories import PlanFactory
from django.conf import settings

class TestLangfuseHandler(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.plan = PlanFactory(user=self.user)
        
    @patch('api.utils.tracing.CallbackHandler')
    def test_handler_initialization_success(self, mock_handler):
        handler = get_langfuse_handler(self.plan, self.user)
        
        mock_handler.assert_called_once_with(
            host="https://us.cloud.langfuse.com",
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            session_id=str(self.plan.id),
            user_id=str(self.user.id)
        )
        self.assertIsNotNone(handler)
        
    def test_handler_missing_plan(self):
        handler = get_langfuse_handler(None, self.user)
        self.assertIsNone(handler)
        
    def test_handler_missing_user(self):
        handler = get_langfuse_handler(self.plan, None)
        self.assertIsNone(handler)
        
    @patch('api.utils.tracing.CallbackHandler')
    def test_handler_initialization_error(self, mock_handler):
        mock_handler.side_effect = Exception("Test error")
        handler = get_langfuse_handler(self.plan, self.user)
        self.assertIsNone(handler)