from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


def sample_user(email='ali@test.com', password='testpass'):
    """Creates a sample user"""
    return get_user_model().objects.create_user(email, password)


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

    def test_tag_str(self):
        """Test tag string representation"""
        tag = models.Tag.objects.create(user=sample_user(), name='Vegan')
        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """Test the ingredient string representation"""
        ingredient = models.Ingredient.objects.create(user=sample_user(),
                                                      name="Cucumber")
        self.assertEqual(str(ingredient), ingredient.name)
