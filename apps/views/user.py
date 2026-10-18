from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Follow, Report, User
from apps.serializers import (
    FCMTokenSerializer,
    MeSerializer,
    UserPublicSerializer,
    UserReportSerializer,
)


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


class FollowByPhoneToggleView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Telefon raqam bo'yicha foydalanuvchini kuzatish / kuzatishni bekor qilish",
        request=None,
        responses={
            200: OpenApiResponse(description="Kuzatish bekor qilindi (unfollowed)"),
            201: OpenApiResponse(description="Foydalanuvchi kuzatila boshlandi (followed)"),
            400: OpenApiResponse(description="O'zingizni kuzatib bo'lmaydi"),
            404: OpenApiResponse(description="Foydalanuvchi topilmadi"),
        },
        tags=["Users"],
    )
    def post(self, request, phone):
        from apps.utils.phone import normalize_phone
        normalized = normalize_phone(phone)
        try:
            target_user = User.objects.get(phone=normalized)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if target_user == request.user:
            return Response({'error': 'You cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
        follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)

        if not created:
            follow.delete()
            return Response({'message': 'Unfollowed'}, status=status.HTTP_200_OK)

        return Response({'message': 'Followed'}, status=status.HTTP_201_CREATED)

    def delete(self, request, phone):
        from apps.utils.phone import normalize_phone
        normalized = normalize_phone(phone)
        try:
            target_user = User.objects.get(phone=normalized)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        Follow.objects.filter(follower=request.user, following=target_user).delete()
        return Response({'message': 'Unfollowed'}, status=status.HTTP_204_NO_CONTENT)


class UserReportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Foydalanuvchini shikoyat qilish",
        request=UserReportSerializer,
        responses={
            201: OpenApiResponse(description="Shikoyat qabul qilindi"),
            200: OpenApiResponse(description="Shikoyat allaqachon yuborilgan (de-dupe)"),
        },
        tags=["Users"],
    )
    def post(self, request):
        serializer = UserReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_user = serializer.validated_data["phone"]  # validate_phone returns User object

        if target_user == request.user:
            raise ValidationError("O'zingizni shikoyat qila olmaysiz.")

        existing = Report.objects.filter(
            reporter=request.user, target_user=target_user
        ).exists()
        if existing:
            return Response(status=status.HTTP_200_OK)

        Report.objects.create(
            reporter=request.user,
            target_user=target_user,
            reason_codes=serializer.validated_data["reason_codes"],
            comment=serializer.validated_data.get("message", ""),
        )
        return Response(status=status.HTTP_201_CREATED)


class UserFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="FCM tokenni ro'yxatdan o'tkazish",
        request=FCMTokenSerializer,
        responses={200: OpenApiResponse(description="Token saqlandi")},
        tags=["Users"],
    )
    def post(self, request):
        serializer = FCMTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.fcm_token = serializer.validated_data["token"]
        request.user.save(update_fields=["fcm_token"])
        return Response(status=status.HTTP_200_OK)


class UserFollowingListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Kuzatilayotgan foydalanuvchilar ro'yxati",
        responses={200: UserPublicSerializer(many=True)},
        tags=["Users"],
    )
    def get(self, request):
        following_users = User.objects.filter(followers__follower=request.user)
        serializer = UserPublicSerializer(following_users, many=True, context={"request": request})
        return Response(serializer.data)


class UserStatsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Sotuvchi statistikasi",
        responses={200: OpenApiResponse(description="Statistika ma'lumotlari")},
        tags=["Users"],
    )
    def get(self, request):
        days = request.query_params.get("days", "30")
        try:
            int(days)
        except ValueError:
            pass

        active_listings_count = request.user.listings.filter(status="active").count()

        data = {
            "totals": {
                "listing_views": 0,
                "reel_views": 0,
                "active_listings": active_listings_count,
                "profile_views": 0,
                "contact_clicks": 0,
                "chats": 0,
            },
            "has_contact_stats": False,
            "daily": [],
            "per_listing": [],
        }
        for listing in request.user.listings.all():
            data["per_listing"].append({
                "id": str(listing.id),
                "title": getattr(listing, "title", ""),
                "views": 0,
                "reel_views": 0,
                "has_reel": False,
                "image": listing.images.first().image.url if listing.images.exists() else None,
            })
        return Response(data)

