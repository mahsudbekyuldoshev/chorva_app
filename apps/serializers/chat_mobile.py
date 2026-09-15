from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.models import Conversation, Message, User


class ChatOtherUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    phone = serializers.CharField()
    full_name = serializers.CharField()
    avatar_url = serializers.SerializerMethodField()
    is_verified = serializers.BooleanField()
    is_online = serializers.SerializerMethodField()
    last_seen_at = serializers.DateTimeField()

    def get_avatar_url(self, obj):
        request = self.context.get("request")
        if not obj.avatar:
            return None
        url = obj.avatar.url
        return request.build_absolute_uri(url) if request else url

    def get_is_online(self, obj):
        if not obj.last_seen_at:
            return False
        return (timezone.now() - obj.last_seen_at) < timedelta(minutes=5)


class ChatProductSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        media = obj.media.filter(media_type="image").first()
        if not media:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(media.file.url) if request else media.file.url


class ChatSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    last_message_text = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "other_user", "product", "last_message_text",
                  "last_message_at", "created_at", "unread_count")

    def get_other_user(self, obj):
        request = self.context.get("request")
        me = request.user
        other = obj.seller if obj.buyer == me else obj.buyer
        return ChatOtherUserSerializer(other, context=self.context).data

    def get_product(self, obj):
        if not obj.listing:
            return None
        return ChatProductSerializer(obj.listing, context=self.context).data

    def _last_message(self, obj):
        return obj.messages.order_by("-created_at").first()

    def get_last_message_text(self, obj):
        msg = self._last_message(obj)
        return msg.text if msg else None

    def get_last_message_at(self, obj):
        msg = self._last_message(obj)
        return msg.created_at if msg else None

    def get_unread_count(self, obj):
        request = self.context.get("request")
        return obj.messages.filter(read_at__isnull=True).exclude(sender=request.user).count()


class ChatCreateSerializer(serializers.Serializer):
    other_phone = serializers.CharField()
    product_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_other_phone(self, value):
        try:
            return User.objects.get(phone=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Foydalanuvchi topilmadi.")

    def create(self, validated_data):
        from apps.models import Listing
        request = self.context["request"]
        other_user = validated_data["other_phone"]
        product_id = validated_data.get("product_id")
        listing = Listing.objects.filter(id=product_id).first() if product_id else None

        conversation, _ = Conversation.objects.get_or_create(
            buyer=request.user, seller=other_user, listing=listing
        )
        return conversation


class ChatMessageSerializer(serializers.ModelSerializer):
    conversation_id = serializers.UUIDField(source="conversation.id", read_only=True)
    sender_id = serializers.UUIDField(source="sender.id", read_only=True)
    body = serializers.CharField(source="text")

    class Meta:
        model = Message
        fields = ("id", "conversation_id", "sender_id", "body", "created_at", "read_at")
        read_only_fields = ("id", "conversation_id", "sender_id", "created_at", "read_at")
