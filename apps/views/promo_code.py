from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import PromoCode
from apps.serializers.promo_code import PromoCodeCheckSerializer, PromoCodeSerializer


@extend_schema(summary="O'zining promo kodlari", tags=["Promo"])
class PromoCodeMineListView(generics.ListAPIView):
    serializer_class = PromoCodeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return PromoCode.objects.filter(user=self.request.user)


@extend_schema(summary="Promo kodni tekshirish", tags=["Promo"])
class PromoCodeCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, code):
        promo = PromoCode.objects.filter(code=code).first()
        if not promo:
            raise NotFound("Promo kod topilmadi.")
        if promo.user != request.user:
            raise PermissionDenied("Bu promo kod sizga tegishli emas.")
        if promo.used:
            raise ValidationError("Bu promo kod allaqachon ishlatilgan.")
        return Response(PromoCodeCheckSerializer(promo).data)
