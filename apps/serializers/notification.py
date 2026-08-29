from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from apps.models import Notification

class NotificationSerializer(ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'type', 'title', 'body', 'is_read', 'created_at')
