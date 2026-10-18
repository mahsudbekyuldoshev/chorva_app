import pytest
from django.urls import reverse
from rest_framework import status

from apps.models import Follow


@pytest.mark.django_db
def test_follow_toggle_flow(api_client, auth_client, user, other_user):
    # Follow
    url = reverse('follow-toggle', kwargs={'id': other_user.id})
    response = auth_client.post(url)
    assert response.status_code == status.HTTP_201_CREATED
    assert Follow.objects.filter(follower=user, following=other_user).exists()
    
    # Unfollow
    response = auth_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    assert not Follow.objects.filter(follower=user, following=other_user).exists()


@pytest.mark.django_db
def test_follow_by_phone_flow(api_client, auth_client, user, other_user):
    url = reverse('follow-toggle-phone', kwargs={'phone': other_user.phone})
    response = auth_client.post(url)
    assert response.status_code == status.HTTP_201_CREATED
    assert Follow.objects.filter(follower=user, following=other_user).exists()

    # Delete (unfollow)
    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Follow.objects.filter(follower=user, following=other_user).exists()

@pytest.mark.django_db
def test_cannot_follow_self(auth_client, user):
    url = reverse('follow-toggle', kwargs={'id': user.id})
    response = auth_client.post(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_me_endpoint_new_path_and_fields(auth_client, user):
    response = auth_client.get(reverse('me'))

    assert response.status_code == 200
    for key in ("bio", "avatar_url", "posts_count", "followers_count",
                "following_count", "rating", "rating_count", "tier_id", "tier_name"):
        assert key in response.data


@pytest.mark.django_db
def test_public_profile_shape(api_client, user):
    response = api_client.get(reverse('user-detail', kwargs={'id': user.id}))

    assert response.status_code == 200
    for key in ("phone", "bio", "avatar_url", "posts_count",
                "followers_count", "rating", "rating_count", "tier_id", "tier_name"):
        assert key in response.data


@pytest.mark.django_db
def test_authenticated_request_updates_last_seen(api_client, user):
    from rest_framework_simplejwt.tokens import RefreshToken

    assert user.last_seen_at is None
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    response = api_client.get(reverse('me'))

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.last_seen_at is not None


def test_normalize_phone():
    from apps.utils.phone import normalize_phone
    assert normalize_phone("+998901234567") == "998901234567"
    assert normalize_phone("998901234567") == "998901234567"
    assert normalize_phone("901234567") == "998901234567"
    assert normalize_phone("+998 90 123 45 67") == "998901234567"
    assert normalize_phone("") == ""
    assert normalize_phone(None) == ""


@pytest.mark.django_db
@pytest.mark.parametrize("phone_format", [
    "998903333333",
    "+998903333333",
    "903333333",
    "+998 90 333 33 33",
])
def test_follow_by_phone_flow_various_formats(api_client, auth_client, user, other_user, phone_format):
    other_user.phone = "998903333333"
    other_user.save()

    url = reverse('follow-toggle-phone', kwargs={'phone': phone_format})
    response = auth_client.post(url)
    assert response.status_code == status.HTTP_201_CREATED
    assert Follow.objects.filter(follower=user, following=other_user).exists()

    url_del = reverse('follow-toggle-phone', kwargs={'phone': "903333333"})
    response = auth_client.delete(url_del)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Follow.objects.filter(follower=user, following=other_user).exists()


@pytest.mark.django_db
def test_fcm_token_success(auth_client, user):
    url = reverse('user-fcm-token')
    response = auth_client.post(url, {"token": "test-fcm-token-123"})
    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.fcm_token == "test-fcm-token-123"


@pytest.mark.django_db
def test_fcm_token_unauthenticated(api_client):
    url = reverse('user-fcm-token')
    response = api_client.post(url, {"token": "test-fcm-token-123"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_following_list_success(auth_client, user, other_user):
    Follow.objects.create(follower=user, following=other_user)
    url = reverse('user-following')
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["id"] == str(other_user.id)


@pytest.mark.django_db
def test_following_list_unauthenticated(api_client):
    url = reverse('user-following')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_stats_me_success_default_days(auth_client, user, category):
    from datetime import timedelta

    from django.utils import timezone

    from apps.models import Listing
    Listing.objects.create(
        user=user, category=category, title="My Listing", price=10000,
        lat=0, lng=0, address_text="Tashkent", view_count=10, status="active",
        expires_at=timezone.now() + timedelta(days=30)
    )
    url = reverse('user-stats')
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["totals"]["listing_views"] == 10
    assert response.data["totals"]["active_listings"] == 1
    assert len(response.data["per_listing"]) == 1


@pytest.mark.django_db
def test_stats_me_custom_days_valid(auth_client, user):
    url = reverse('user-stats') + "?days=7"
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    url365 = reverse('user-stats') + "?days=365"
    response365 = auth_client.get(url365)
    assert response365.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_stats_me_invalid_days(auth_client, user):
    url = reverse('user-stats') + "?days=0"
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    url366 = reverse('user-stats') + "?days=366"
    response366 = auth_client.get(url366)
    assert response366.status_code == status.HTTP_400_BAD_REQUEST

    url_abc = reverse('user-stats') + "?days=abc"
    response_abc = auth_client.get(url_abc)
    assert response_abc.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_stats_me_excludes_other_users_listings(auth_client, user, other_user, category):
    from datetime import timedelta

    from django.utils import timezone

    from apps.models import Listing
    Listing.objects.create(
        user=user, category=category, title="My Listing", price=10000,
        lat=0, lng=0, address_text="Tashkent", view_count=5, status="active",
        expires_at=timezone.now() + timedelta(days=30)
    )
    Listing.objects.create(
        user=other_user, category=category, title="Other Listing", price=20000,
        lat=0, lng=0, address_text="Samarkand", view_count=100, status="active",
        expires_at=timezone.now() + timedelta(days=30)
    )
    url = reverse('user-stats')
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["totals"]["listing_views"] == 5
    assert response.data["totals"]["active_listings"] == 1
    assert len(response.data["per_listing"]) == 1
    assert response.data["per_listing"][0]["title"] == "My Listing"


@pytest.mark.django_db
def test_stats_me_unauthenticated(api_client):
    url = reverse('user-stats')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

