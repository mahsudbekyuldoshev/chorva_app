import pytest
from django.urls import reverse
from rest_framework import status

from apps.models import Notification


@pytest.mark.django_db
def test_notifications_require_auth(api_client):
    response = api_client.get(reverse('notification-list'))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_user_sees_only_own_notifications(api_client, auth_client, user, other_user):
    Notification.objects.create(user=user, type="message", title="User N")
    Notification.objects.create(user=other_user, type="message", title="Other N")
    
    response = auth_client.get(reverse('notification-list'))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['title'] == "User N"
