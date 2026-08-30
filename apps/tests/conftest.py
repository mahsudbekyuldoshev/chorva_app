import pytest
from rest_framework.test import APIClient

from apps.models import Category, Conversation, User


@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return User.objects.create_user(phone="998901111111", password="password")

@pytest.fixture
def verified_user():
    return User.objects.create_user(phone="998902222222", password="password", is_verified=True)

@pytest.fixture
def other_user():
    return User.objects.create_user(phone="998903333333", password="password")

@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.fixture
def category():
    return Category.objects.create(name_uz="Sigirlar", name_ru="Коровы", name_en="Cows")

@pytest.fixture
def conversation(user, other_user, category):
    return Conversation.objects.create(buyer=user, seller=other_user, listing=None)
