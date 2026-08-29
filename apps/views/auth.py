from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.models import User
from apps.serializers import RequestOTPSerializer, VerifyOTPSerializer
from apps.services import generate_otp, verify_otp


class RequestOTPView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_request"
    permission_classes = []

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        otp, error = generate_otp(phone)

        if error:
            return Response({"error": error}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        return Response({"message": "OTP sent"})


class VerifyOTPView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_verify"
    permission_classes = []

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]

        if verify_otp(phone, code):
            user, created = User.objects.get_or_create(phone=phone)
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": {"id": user.id, "phone": user.phone},
                    "is_new_user": created,
                }
            )

        return Response({"error": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)
