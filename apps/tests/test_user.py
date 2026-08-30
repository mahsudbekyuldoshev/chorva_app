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
