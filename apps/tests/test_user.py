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
