from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, OpenApiTypes, extend_schema, extend_schema_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated

from apps.models import Conversation, Message, Notification
from apps.permission import IsParticipant
from apps.serializers.chat import (
    ConversationCreateSerializer,
    ConversationSerializer,
    MessageSerializer,
)


@extend_schema_view(
    get=extend_schema(
        summary="Joriy foydalanuvchining suhbatlari ro'yxati",
        responses={200: ConversationSerializer(many=True)},
        tags=["Chat"],
    ),
    post=extend_schema(
        summary="Yangi suhbat boshlash",
        request=ConversationCreateSerializer,
        responses={
            201: ConversationSerializer,
            400: OpenApiResponse(description="O'zingiz bilan suhbat ochib bo'lmaydi"),
        },
        tags=["Chat"],
    ),
)
class ConversationListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ConversationCreateSerializer
        return ConversationSerializer

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(Q(buyer=user) | Q(seller=user)).order_by(
            "-updated_at"
        )


@extend_schema_view(
    get=extend_schema(
        summary="Suhbatdagi xabarlar tarixi",
        parameters=[OpenApiParameter("conversation_id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
        responses={
            200: MessageSerializer(many=True),
            403: OpenApiResponse(description="Bu suhbat ishtirokchisi emassiz"),
        },
        tags=["Chat"],
    ),
    post=extend_schema(
        summary="Suhbatga yangi xabar yozish",
        request=MessageSerializer,
        parameters=[OpenApiParameter("conversation_id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
        responses={
            201: MessageSerializer,
            403: OpenApiResponse(description="Bu suhbat ishtirokchisi emassiz"),
        },
        tags=["Chat"],
    ),
)
class MessageListCreateView(ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsParticipant]

    def get_conversation(self):
        conversation = get_object_or_404(Conversation, pk=self.kwargs["conversation_id"])
        if self.request.user != conversation.buyer and self.request.user != conversation.seller:
            raise PermissionDenied("You are not a participant in this conversation.")
        return conversation

    def get_queryset(self):
        conversation = self.get_conversation()
        return Message.objects.filter(conversation=conversation)

    def perform_create(self, serializer):
        conversation = self.get_conversation()
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
        conversation.save()
