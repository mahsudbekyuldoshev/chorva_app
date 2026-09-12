from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.models import User
from apps.serializers import RequestOTPSerializer, VerifyOTPSerializer
from apps.services.otp import generate_otp, verify_otp


@extend_schema(
    summary="OTP kodini so'rash",
    request=RequestOTPSerializer,
    responses={200: OpenApiResponse(description="OTP kod yuborildi")},
    tags=["Auth"],
)
class RequestOTPView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        _, error = generate_otp(phone)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "OTP sent"})


@extend_schema(
    summary="OTP kodini tekshirish",
    request=VerifyOTPSerializer,
    responses={
        200: OpenApiResponse(description="Tokenlar va foydalanuvchi ma'lumotlari"),
        400: OpenApiResponse(description="Noto'g'ri kod"),
    },
    tags=["Auth"],
)
class VerifyOTPView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]

        if verify_otp(phone, code):
            user, created = User.objects.get_or_create(phone=phone)
            if created:
                user.set_unusable_password()
                user.save()
                from apps.models import Plan, Subscription

                free_plan = Plan.objects.filter(slug="free").first()
                if free_plan:
                    Subscription.objects.create(user=user, plan=free_plan, expires_at=None)

            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "is_new_user": created,
                    "user_id": str(user.id),
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                }
            )

        return Response({"error": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)


class MobileTokenRefreshSerializer(TokenRefreshSerializer):
    def to_internal_value(self, data):
        data = data.copy()
        if "refresh_token" in data and "refresh" not in data:
            val = data.pop("refresh_token")
            data["refresh"] = val[0] if isinstance(val, list) else val
        return super().to_internal_value(data)

    def validate(self, attrs):
        result = super().validate(attrs)
        output = {"access_token": result["access"]}
        if "refresh" in result:
            output["refresh_token"] = result["refresh"]
        return output


class MobileTokenRefreshView(TokenRefreshView):
    serializer_class = MobileTokenRefreshSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:  # noqa: S110, BLE001
                pass  # mobil ilova xatolikni e'tiborsiz qoldiradi (hujjatga ko'ra)
        return Response(status=204)
