from django.db.models import Q
from rest_framework.generics import ListCreateAPIView

from apps.models import Conversation, Message, Notification
from apps.permission import IsParticipant
from apps.serializers.chat import (
    ConversationCreateSerializer,
    ConversationSerializer,
    MessageSerializer,
)


class ConversationListCreateView(ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "POST":
            return ConversationCreateSerializer
        return ConversationSerializer

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(Q(buyer=user) | Q(seller=user)).order_by(
            "-updated_at"
        )


class MessageListCreateView(ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsParticipant]

    def get_queryset(self):
        return Message.objects.filter(conversation_id=self.kwargs["conversation_id"])

    def perform_create(self, serializer):
        conversation = Conversation.objects.get(id=self.kwargs["conversation_id"])
        serializer.save(sender=self.request.user, conversation=conversation)

        # Create notification for recipient
        recipient = (
            conversation.seller
            if self.request.user == conversation.buyer
            else conversation.buyer
        )
        Notification.objects.create(
            user=recipient,
            type="message",
            title="New message",
            body=serializer.validated_data["text"][:100],
        )
        conversation.save()  # Update updated_at
