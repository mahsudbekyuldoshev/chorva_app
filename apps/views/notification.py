from rest_framework import generics, status
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.response import Response

from apps.models import Notification
from apps.serializers.notification import NotificationSerializer


class NotificationListView(ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )


class NotificationMarkReadView(UpdateAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"status": "marked as read"})
