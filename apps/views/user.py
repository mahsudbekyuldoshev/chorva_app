from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Follow, User
from apps.serializers import MeSerializer, UserPublicSerializer


@extend_schema_view(
    retrieve=extend_schema(
        summary="Joriy foydalanuvchi profilini olish",
        responses={200: MeSerializer},
        tags=["Users"],
    ),
    update=extend_schema(
        summary="Profilni to'liq yangilash",
        request=MeSerializer,
        responses={200: MeSerializer},
        tags=["Users"],
    ),
    partial_update=extend_schema(
        summary="Profilni qisman yangilash",
        request=MeSerializer,
        responses={200: MeSerializer},
        tags=["Users"],
    ),
)
class MeView(RetrieveUpdateAPIView):
    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema_view(
    retrieve=extend_schema(
        summary="Boshqa foydalanuvchining ochiq profilini ko'rish",
        responses={
            200: UserPublicSerializer,
            404: OpenApiResponse(description="Foydalanuvchi topilmadi"),
        },
        tags=["Users"],
    ),
)
class UserPublicDetailView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserPublicSerializer
    permission_classes = []
    lookup_field = 'id'


class FollowToggleView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Foydalanuvchini kuzatish / kuzatishni bekor qilish",
        description="Agar hali kuzatilmagan bo'lsa — follow qiladi (201). Agar allaqachon kuzatilayotgan bo'lsa — unfollow qiladi (200).",
        request=None,
        responses={
            200: OpenApiResponse(description="Kuzatish bekor qilindi (unfollowed)"),
            201: OpenApiResponse(description="Foydalanuvchi kuzatila boshlandi (followed)"),
            400: OpenApiResponse(description="O'zingizni kuzatib bo'lmaydi"),
            404: OpenApiResponse(description="Foydalanuvchi topilmadi"),
        },
        tags=["Users"],
    )
    def post(self, request, id):
        try:
            target_user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if target_user == request.user:
            return Response({'error': 'You cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
        follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)

        if not created:
            follow.delete()
            return Response({'message': 'Unfollowed'}, status=status.HTTP_200_OK)

        return Response({'message': 'Followed'}, status=status.HTTP_201_CREATED)
