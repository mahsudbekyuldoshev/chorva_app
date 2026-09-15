import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_create_chat_by_phone(auth_client, verified_user, other_user):
    auth_client.force_authenticate(user=verified_user)

    response = auth_client.post(reverse('chat-list'), {"other_phone": other_user.phone})

    assert response.status_code == 201
    assert "other_user" in response.data
    assert response.data["other_user"]["phone"] == other_user.phone

@pytest.mark.django_db
def test_send_message_uses_body_field(auth_client, verified_user, other_user):
    from apps.models import Conversation
    conversation = Conversation.objects.create(buyer=verified_user, seller=other_user)
    auth_client.force_authenticate(user=verified_user)

    response = auth_client.post(
        reverse('chat-messages', kwargs={'conversation_id': conversation.id}),
        {"body": "Salom"},
    )

    assert response.status_code == 201
    assert response.data["body"] == "Salom"

@pytest.mark.django_db
def test_chat_mark_read_updates_read_at(auth_client, verified_user, other_user):
    from apps.models import Conversation, Message
    conversation = Conversation.objects.create(buyer=verified_user, seller=other_user)
    message = Message.objects.create(conversation=conversation, sender=other_user, text="Salom")
    auth_client.force_authenticate(user=verified_user)

    response = auth_client.patch(reverse('chat-read', kwargs={'conversation_id': conversation.id}))

    assert response.status_code == 204
    message.refresh_from_db()
    assert message.read_at is not None
