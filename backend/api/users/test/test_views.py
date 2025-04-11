import factory
from unittest.mock import patch
from faker import Faker

from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from api.users.models import User

from .factories import UserFactory


fake = Faker()


class TestUserListTestCase(APITestCase):
    """
    Tests /users list operations.
    """

    def setUp(self):
        self.url = reverse('user-list')
        self.user_data = {
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': fake.email(),
            'password': fake.password(),
        }

    def test_post_request_with_no_data_fails(self):
        """"
        Test that a POST request with no data fails.
        """
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_request_with_valid_data_succeeds(self):
        """
        Test that a POST request with valid data succeeds.
        """
        response = self.client.post(
            self.url, self.user_data,
            HTTP_ORIGIN='http://new.example.com'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(pk=response.data.get('id'))
        self.assertEqual(user.email, self.user_data.get('email'))
        self.assertEqual(user.first_name, self.user_data.get('first_name'))
        self.assertEqual(user.last_name, self.user_data.get('last_name'))
        self.assertEqual(str(user.auth_token), response.data.get('auth_token'))


class TestUserDetailTestCase(APITestCase):
    """
    Tests /users detail operations.
    """

    def setUp(self):
        self.user = UserFactory()
        self.url = reverse('user-detail', kwargs={'pk': self.user.pk})
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}'
        )

    def test_get_request_returns_a_given_user(self):
        """
        Test that a GET request returns a given user.
        """
        response = self.client.get(
            self.url, HTTP_ORIGIN='http://new.example.com'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_request_updates_a_user(self):
        """
        Test that a PUT request updates a user.
        """
        new_first_name = fake.first_name()
        payload = {'first_name': new_first_name}
        response = self.client.put(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the user was updated
        user = User.objects.get(pk=self.user.id)
        self.assertEqual(user.first_name, new_first_name)


class CurrentUserViewTest(APITestCase):
    """
    Tests for the /users/me endpoint.
    """

    def test_get_current_user(self):
        """
        Test that a GET request to the /users/me/ endpoint returns the 
        currently authenticated user.
        """
        user = UserFactory()
        self.client.force_authenticate(user=user)
        url = reverse('user-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], user.email)

class TestUserPatchTestCase(APITestCase):
    """
    Tests /users PATCH operations for updating user and profile data.
    """

    def setUp(self):
        self.user = UserFactory()
        self.url = reverse('user-detail', kwargs={'pk': self.user.pk})
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}'
        )

    def test_patch_request_updates_user_partially(self):
        """
        Test that a PATCH request updates only the provided fields.
        """
        new_first_name = fake.first_name()
        payload = {'first_name': new_first_name}
        response = self.client.patch(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the user was updated
        user = User.objects.get(pk=self.user.id)
        self.assertEqual(user.first_name, new_first_name)
        
        # Check that other fields were not changed
        self.assertEqual(user.last_name, self.user.last_name)

    def test_patch_request_updates_profile_partially(self):
        """
        Test that a PATCH request updates nested profile fields.
        """
        profile_data = {'profile': {'age': 30}}
        response = self.client.patch(self.url, profile_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the profile was updated
        user = User.objects.get(pk=self.user.id)
        self.assertEqual(user.profile.age, 30)

    def test_patch_request_with_invalid_age(self):
        """
        Test that PATCH request with invalid age returns validation error.
        """
        profile_data = {'profile': {'age': 15}}  # Below minimum age
        response = self.client.patch(self.url, profile_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('profile', response.data)
        self.assertIn('age', response.data['profile'])

    def test_patch_request_with_invalid_height(self):
        """
        Test that PATCH request with invalid height returns validation error.
        """
        profile_data = {'profile': {'feet': 10}}  # Above maximum feet
        response = self.client.patch(self.url, profile_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('profile', response.data)
        self.assertIn('feet', response.data['profile'])

    def test_patch_request_with_invalid_weight(self):
        """
        Test that PATCH request with invalid weight returns validation error.
        """
        profile_data = {'profile': {'weightKg': 600}}  # Above maximum kg
        response = self.client.patch(self.url, profile_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('profile', response.data)
        self.assertIn('weightKg', response.data['profile'])

    def test_patch_request_with_invalid_json_field(self):
        """
        Test that PATCH request with invalid JSON field returns validation error.
        """
        profile_data = {'profile': {'goals': {'goal': 'invalid_goal'}}}
        response = self.client.patch(self.url, profile_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('profile', response.data)
        self.assertIn('goals', response.data['profile'])

    def test_patch_request_with_valid_json_field(self):
        """
        Test that PATCH request with valid JSON field passes validation.
        """
        profile_data = {'profile': {'goals': ['weight_loss', 'improve_fitness']}}
        response = self.client.patch(self.url, profile_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the profile was updated
        user = User.objects.get(pk=self.user.id)
        self.assertEqual(user.profile.goals, ['weight_loss', 'improve_fitness'])

    def test_patch_request_with_valid_date(self):
        """
        Test that PATCH request with valid date passes validation.
        """
        import datetime
        future_date = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
        profile_data = {'profile': {'raceDate': future_date}}
        response = self.client.patch(self.url, profile_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_request_unauthorized(self):
        """
        Test that PATCH request without authentication returns 401.
        """
        # Remove credentials
        self.client.credentials()
        profile_data = {'profile': {'age': 30}}
        response = self.client.patch(self.url, profile_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_request_other_user(self):
        """
        Test that PATCH request for another user's data returns 403.
        """
        other_user = UserFactory()
        other_url = reverse('user-detail', kwargs={'pk': other_user.pk})
        profile_data = {'profile': {'age': 30}}
        response = self.client.patch(other_url, profile_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)