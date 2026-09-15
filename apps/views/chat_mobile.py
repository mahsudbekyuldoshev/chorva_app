from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Conversation, Notification
from apps.serializers.chat_mobile import (
    ChatCreateSerializer,
    ChatMessageSerializer,
    ChatSerializer,
)


@extend_schema_view(
    get=extend_schema(summary="Suhbatlar ro'yxati", tags=["Chat"]),
    post=extend_schema(summary="Suhbat yaratish/olish", tags=["Chat"]),
)
class ChatListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return ChatCreateSerializer if self.request.method == "POST" else ChatSerializer

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(Q(buyer=user) | Q(seller=user)).order_by("-updated_at")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        output = ChatSerializer(conversation, context=self.get_serializer_context())
        return Response(output.data, status=201)


@extend_schema_view(
    get=extend_schema(summary="Suhbat xabarlari", tags=["Chat"]),
    post=extend_schema(summary="Xabar yuborish", tags=["Chat"]),
)
class ChatMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_conversation(self):
        conversation = get_object_or_404(Conversation, pk=self.kwargs["conversation_id"])
        if self.request.user not in (conversation.buyer, conversation.seller):
            raise PermissionDenied("Bu suhbat ishtirokchisi emassiz.")
        return conversation

    def get_queryset(self):
        conversation = self.get_conversation()
        qs = conversation.messages.select_related("sender").order_by("created_at")
        before = self.request.query_params.get("before")
        if before:
            qs = qs.filter(created_at__lt=before)
        return qs

    def perform_create(self, serializer):
        conversation = self.get_conversation()
        message = serializer.save(sender=self.request.user, conversation=conversation)

        recipient = conversation.seller if self.request.user == conversation.buyer else conversation.buyer
        Notification.objects.create(
            user=recipient, type="message", title="Yangi xabar", body=message.text[:200],
        )


@extend_schema(summary="Suhbatni o'qilgan deb belgilash", tags=["Chat"])
class ChatMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, pk=conversation_id)
        if request.user not in (conversation.buyer, conversation.seller):
            raise PermissionDenied("Bu suhbat ishtirokchisi emassiz.")
        conversation.messages.filter(read_at__isnull=True).exclude(
            sender=request.user
        ).update(read_at=timezone.now())
        return Response(status=204)
