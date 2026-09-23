from django.db.models import F
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.models import Banner
from apps.serializers.banner import BannerSerializer


@extend_schema(summary="Banner/story ro'yxati", tags=["Banners"])
class BannerListView(generics.ListAPIView):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    permission_classes = []
    pagination_class = None


@extend_schema(summary="Banner ko'rilganini qayd etish", tags=["Banners"])
class BannerViewIncrementView(APIView):
    permission_classes = []

    def post(self, request, pk):
        banner = get_object_or_404(Banner, pk=pk)
        Banner.objects.filter(pk=pk).update(view_count=F("view_count") + 1)
        banner.refresh_from_db(fields=["view_count"])
        return Response({"view_count": banner.view_count})
