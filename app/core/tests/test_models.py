from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        '''Test creating a new user with an email address is successful'''
        email = 'test@test.com'
        password = 'Testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user if normalized or not."""
        email = 'test@TEST.com'
        password = 'Testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password)
        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating a new user with invalid email will raise an error"""
        with self.assertRaises(ValueError):
            email = None
            password = 'Testpass123'
            get_user_model().objects.create_user(
                email=email,
                password=password
            )

    def test_new_user_is_superuser(self):
        """Test if a super user can be created"""
        email = 'test@test.com'
        password = 'Testpass123'
        user = get_user_model().objects.create_superuser(email=email,
                                                         password=password)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
