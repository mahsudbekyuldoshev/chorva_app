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
    assert len(response.data) == 1
    assert response.data[0]['title'] == "User N"


@pytest.mark.django_db
def test_unread_count(auth_client, user, other_user):
    from apps.models import Notification
    Notification.objects.create(user=user, type="message", title="A", is_read=False)
    Notification.objects.create(user=user, type="message", title="B", is_read=True)
    auth_client.force_authenticate(user=user)

    response = auth_client.get(reverse('notification-unread-count'))

    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_mark_all_read(auth_client, user):
    from apps.models import Notification
    Notification.objects.create(user=user, type="message", title="A", is_read=False)
    Notification.objects.create(user=user, type="message", title="B", is_read=False)
    auth_client.force_authenticate(user=user)

    response = auth_client.patch(reverse('notification-read-all'))

    assert response.status_code == 204
    assert Notification.objects.filter(user=user, is_read=False).count() == 0

