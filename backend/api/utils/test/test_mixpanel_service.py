from django.test import TestCase, RequestFactory, override_settings
from unittest.mock import patch, MagicMock
from api.users.test.factories import UserFactory
from api.utils.mixpanel_service import MixpanelService

class TestMixpanelService(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory()

    @override_settings(MIXPANEL_ENABLED=True)
    @patch('api.utils.mixpanel_service.Mixpanel')
    def test_track_event_with_request(self, mock_mixpanel_class):
        mock_mp_instance = MagicMock()
        mock_mixpanel_class.return_value = mock_mp_instance

        service = MixpanelService()
        service.enabled = True  # Ensure tracking is active

        request = self.factory.get('/?utm_source=test')
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'

        service.track(
            str(self.user.id),
            'Test Event',
            {'custom': 'data'},
            request
        )

        mock_mp_instance.track.assert_called_once()
        args = mock_mp_instance.track.call_args[0]
        self.assertEqual(args[0], str(self.user.id))
        self.assertEqual(args[1], 'Test Event')
        self.assertIn('utm_source', args[2])
        self.assertIn('browser', args[2])

    @override_settings(MIXPANEL_ENABLED=True)
    @patch('api.utils.mixpanel_service.Mixpanel')
    def test_track_event_without_request(self, mock_mixpanel_class):
        mock_mp_instance = MagicMock()
        mock_mixpanel_class.return_value = mock_mp_instance

        service = MixpanelService()
        service.enabled = True  # Ensure tracking is active

        service.track(
            str(self.user.id),
            'Test Event',
            {'custom': 'data'}
        )

        mock_mp_instance.track.assert_called_once()
        args = mock_mp_instance.track.call_args[0]
        self.assertEqual(args[0], str(self.user.id))
        self.assertEqual(args[1], 'Test Event')
        self.assertIn('custom', args[2])
