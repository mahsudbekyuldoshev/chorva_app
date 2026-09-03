from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.models import Notification
from apps.serializers.notification import NotificationSerializer


@extend_schema(
    summary="Joriy foydalanuvchi bildirishnomalari ro'yxati",
    responses={200: NotificationSerializer(many=True)},
    tags=["Notifications"],
)
class NotificationListView(ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )


@extend_schema(
    summary="Bildirishnomani o'qilgan deb belgilash",
    request=None,
    responses={200: OpenApiResponse(description="Bildirishnoma o'qilgan deb belgilandi")},
    tags=["Notifications"],
)
class NotificationMarkReadView(UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"status": "marked as read"})
