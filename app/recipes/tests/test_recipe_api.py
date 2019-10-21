import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipes.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipes:recipe-list')


def upload_image_url(recipe_id):
    """Return URL for recipe image uplaod"""
    return reverse('recipes:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse('recipes:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main Course'):
    """Create and return a sample Tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon'):
    """Create and return a sample Ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return sample Recipe"""
    defaults = {
        'title': 'Sample Recipe',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeAPITests(TestCase):
    """Test unauthenicated recipe API access"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required"""
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API Access"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'ali@test.com',
            'testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        sample_recipe(self.user)
        sample_recipe(self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for User"""
        user2 = get_user_model().objects.create_user(
            'test@test.com',
            'testtest123'
        )
        sample_recipe(user2)
        sample_recipe(self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(len(res.data), 1)

    def test_view_recipe_detail(self):
        """Test viewing recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating a basic recipe"""
        payload = {
            'title': 'Chocolate Cheese Cake',
            'time_minutes': 30,
            'price': 5
        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_tags_recipe(self):
        """Test creating a recipe with tags"""
        tag_one = sample_tag(user=self.user, name='Vegan')
        tag_two = sample_tag(user=self.user, name='Dessert')

        payload = {
            'title': 'Chocolate Cheese Cake',
            'time_minutes': 30,
            'price': 5,
            'tags': [tag_one.id, tag_two.id]
        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()

        self.assertEqual(tags.count(), 2)
        self.assertIn(tag_one, tags)
        self.assertIn(tag_two, tags)

    def test_create_tags_ingredients(self):
        """Test creating a recipe with tags"""
        ingredient_one = sample_ingredient(user=self.user, name='Prawns')
        ingredient_two = sample_ingredient(user=self.user, name='Ginger')

        payload = {
            'title': 'Ginger Prawns',
            'time_minutes': 30,
            'price': 5,
            'ingredients': [ingredient_one.id, ingredient_two.id]
        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient_one, ingredients)
        self.assertIn(ingredient_two, ingredients)

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='Curry')

        payload = {
            'title': 'Chicken Tikka',
            'tags': [new_tag.id]
        }

        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.tags.all().count(), 1)
        self.assertEqual(recipe.tags.all().first().name, new_tag.name)

    def test_full_update_recipe(self):
        """Test updating a recipe with put"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        payload = {
            'title': 'Spagetti Carbonara',
            'time_minutes': 25,
            'price': 10
        }

        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        self.assertEqual(recipe.tags.all().count(), 0)


class RecipeImageUploadTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user('ali@test.com',
                                                         'testpass123')
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test uploading an email to recipe"""
        url = upload_image_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url,
                                   {'image': ntf},
                                   format='multipart')
            self.recipe.refresh_from_db()

            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertIn('image', res.data)
            self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = upload_image_url(self.recipe.id)
        res = self.client.post(url, {'image': 'Not image'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipe_by_tags(self):
        """Testing recipes with specific tags"""
        recipe_one = sample_recipe(user=self.user,
                                   title='Thai Vegetable Curry')
        recipe_two = sample_recipe(user=self.user,
                                   title='Aubergine Tahini')

        tag_one = sample_tag(user=self.user, name='Vegan')
        tag_two = sample_tag(user=self.user, name='Vegeterian')

        recipe_one.tags.add(tag_one)
        recipe_two.tags.add(tag_two)

        recipe_three = sample_recipe(user=self.user, title='Fish and Chips')

        res = self.client.get(
            RECIPES_URL,
            {
                'tags': f'{tag_one.id},{tag_two.id}'
            }
        )
        serializer_one = RecipeSerializer(recipe_one)
        serializer_two = RecipeSerializer(recipe_two)
        serializer_three = RecipeSerializer(recipe_three)

        self.assertIn(serializer_one.data, res.data)
        self.assertIn(serializer_two.data, res.data)
        self.assertNotIn(serializer_three.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """Returning recipes with specific ingredients"""
        recipe_one = sample_recipe(user=self.user,
                                   title='Thai Vegetable Curry')
        recipe_two = sample_recipe(user=self.user,
                                   title='Aubergine Tahini')

        ingredient_one = sample_ingredient(user=self.user, name='Curry')
        ingredient_two = sample_ingredient(user=self.user, name='Tahini')

        recipe_one.ingredients.add(ingredient_one)
        recipe_two.ingredients.add(ingredient_two)

        recipe_three = sample_recipe(user=self.user, title='Fish and Chips')

        res = self.client.get(
            RECIPES_URL,
            {
                'ingredients': f'{ingredient_one.id},{ingredient_two.id}'
            }
        )

        serializer_one = RecipeSerializer(recipe_one)
        serializer_two = RecipeSerializer(recipe_two)
        serializer_three = RecipeSerializer(recipe_three)

        self.assertIn(serializer_one.data, res.data)
        self.assertIn(serializer_two.data, res.data)
        self.assertNotIn(serializer_three.data, res.data)
