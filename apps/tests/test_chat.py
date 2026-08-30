import pytest
from django.urls import reverse
from rest_framework import status

from apps.models import Notification, User


@pytest.mark.django_db
def test_cannot_message_others_conversation(api_client, conversation, other_user, user):
    third_user = User.objects.create_user(phone="998904444444", password="password")
    api_client.force_authenticate(user=third_user)
    
    url = reverse('message-list', kwargs={'conversation_id': conversation.id})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_participant_can_read_and_send_messages(api_client, conversation, user, other_user):
    api_client.force_authenticate(user=user)
    url = reverse('message-list', kwargs={'conversation_id': conversation.id})
    
    # Send
    data = {"text": "Hello!"}
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    
    # Read
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1

@pytest.mark.django_db
def test_cannot_create_conversation_with_self(api_client, user):
    api_client.force_authenticate(user=user)
    data = {"seller": user.id}
    response = api_client.post(reverse('conversation-list'), data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_message_creates_notification(api_client, conversation, user, other_user):
    api_client.force_authenticate(user=user)
    url = reverse('message-list', kwargs={'conversation_id': conversation.id})
    
    data = {"text": "Hello!"}
    api_client.post(url, data)
    
    assert Notification.objects.filter(user=other_user, type="message").exists()
