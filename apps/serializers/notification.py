from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from apps.models import Notification


class NotificationSerializer(ModelSerializer):
    read = serializers.BooleanField(source="is_read", read_only=True)

    class Meta:
        model = Notification
        fields = ('id', 'type', 'title', 'body', 'action_type', 'read', 'created_at')
