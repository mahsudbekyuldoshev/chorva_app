from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer, ValidationError

from apps.models import Conversation, Message

from .user import UserPublicSerializer


class MessageSerializer(ModelSerializer):
    sender = UserPublicSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "sender", "text", "is_read", "created_at")


class ConversationSerializer(ModelSerializer):
    buyer = UserPublicSerializer(read_only=True)
    seller = UserPublicSerializer(read_only=True)
    last_message = SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "buyer", "seller", "listing", "last_message", "created_at")

    def get_last_message(self, obj):
        message = obj.messages.last()
        if message:
            return MessageSerializer(message).data
        return None


class ConversationCreateSerializer(ModelSerializer):
    class Meta:
        model = Conversation
        fields = ("id", "seller", "listing")

    def validate(self, attrs):
        user = self.context['request'].user
        if attrs['seller'] == user:
            raise ValidationError("You cannot create a conversation with yourself.")
        return attrs

    def create(self, validated_data):
        buyer = self.context["request"].user
        seller = validated_data["seller"]
        listing = validated_data.get("listing")

        conversation, _ = Conversation.objects.get_or_create(
            buyer=buyer, seller=seller, listing=listing
        )
        return conversation
