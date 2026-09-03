from datetime import timedelta
from math import asin, cos, radians, sin, sqrt

from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.models import Category, Favorite, Listing, Reel, Report
from apps.permission import IsOwnerOrReadOnly, IsVerifiedUser
from apps.serializers import (
    CategorySerializer,
    FavoriteSerializer,
    ListingCreateSerializer,
    ListingDetailSerializer,
    ListingListSerializer,
    ReelSerializer,
    ReportSerializer,
)


# ... (haversine remains same) ...
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r

@extend_schema(
    summary="Kategoriyalar ro'yxati",
    responses={200: CategorySerializer(many=True)},
    tags=["Listings"],
)
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all().order_by("sort_order")
    serializer_class = CategorySerializer
    permission_classes = []

@extend_schema_view(
    list=extend_schema(
        summary="E'lonlar ro'yxatini olish (faqat faol e'lonlar)",
        responses={200: ListingListSerializer(many=True)},
        tags=["Listings"],
    ),
    retrieve=extend_schema(
        summary="E'lon tafsilotlarini olish",
        responses={
            200: ListingDetailSerializer,
            404: OpenApiResponse(description="Topilmadi (masalan boshqa userning pending e'loni)"),
        },
        tags=["Listings"],
    ),
    create=extend_schema(
        summary="Yangi e'lon yaratish",
        request=ListingCreateSerializer,
        responses={
            201: ListingCreateSerializer,
            400: OpenApiResponse(description="Noto'g'ri ma'lumot"),
            403: OpenApiResponse(description="Faqat tasdiqlangan (is_verified) foydalanuvchilar e'lon yarata oladi"),
        },
        tags=["Listings"],
    ),
    update=extend_schema(
        summary="E'lonni to'liq yangilash",
        request=ListingCreateSerializer,
        responses={
            200: ListingCreateSerializer,
            403: OpenApiResponse(description="Faqat egasi tahrirlashi mumkin"),
            404: OpenApiResponse(description="Topilmadi"),
        },
        tags=["Listings"],
    ),
    partial_update=extend_schema(
        summary="E'lonni qisman yangilash",
        request=ListingCreateSerializer,
        responses={200: ListingCreateSerializer, 403: OpenApiResponse(description="Faqat egasi tahrirlashi mumkin")},
        tags=["Listings"],
    ),
    destroy=extend_schema(
        summary="E'lonni o'chirish",
        responses={204: OpenApiResponse(description="O'chirildi"), 403: OpenApiResponse(description="Faqat egasi o'chira oladi")},
        tags=["Listings"],
    ),
    favorite=extend_schema(
        summary="E'lonni sevimlilarga qo'shish (POST) / o'chirish (DELETE)",
        request=None,
        responses={
            201: OpenApiResponse(description="Sevimlilarga qo'shildi"),
            204: OpenApiResponse(description="Sevimlilardan o'chirildi"),
        },
        tags=["Listings"],
    ),
    map=extend_schema(
        summary="Xaritada e'lonlarni ko'rish (radius bo'yicha)",
        parameters=[
            OpenApiParameter("lat", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="Markaziy nuqta kengligi"),
            OpenApiParameter("lng", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="Markaziy nuqta uzunligi"),
            OpenApiParameter("radius_km", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="Radius (km), standart 10"),
        ],
        responses={200: ListingListSerializer(many=True)},
        tags=["Listings"],
    ),
)
class ListingViewSet(ModelViewSet):
    permission_classes = [IsOwnerOrReadOnly]

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsVerifiedUser()]
        if self.action == "favorite":
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        if self.action == "list":
            return Listing.objects.filter(status="active").order_by("-created_at")
        return Listing.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != "active" and (not request.user.is_authenticated or instance.user != request.user):
            raise NotFound()
        return super().retrieve(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == "list":
            return ListingListSerializer
        if self.action == "retrieve":
            return ListingDetailSerializer
        if self.action in ["create", "update", "partial_update"]:
            return ListingCreateSerializer
        return ListingListSerializer

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            status="pending",
            expires_at=timezone.now() + timedelta(days=30)
        )

    @action(detail=True, methods=["post", "delete"])
    def favorite(self, request, pk=None):
        listing = self.get_object()
        if request.method == "POST":
            Favorite.objects.get_or_create(user=request.user, listing=listing)
            return Response({"status": "added to favorites"}, status=status.HTTP_201_CREATED)
        else:
            Favorite.objects.filter(user=request.user, listing=listing).delete()
            return Response({"status": "removed from favorites"}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def map(self, request):
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        radius = float(request.query_params.get("radius_km", 10))

        queryset = Listing.objects.filter(status="active")

        if lat and lng:
            lat = float(lat)
            lng = float(lng)
            all_listings = list(queryset)
            filtered_ids = [
                item.id for item in all_listings
                if haversine(lng, lat, item.lng, item.lat) <= radius
            ]
            queryset = queryset.filter(id__in=filtered_ids)

        serializer = ListingListSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)



@extend_schema(
    summary="Joriy foydalanuvchi sevimli e'lonlari",
    responses={200: FavoriteSerializer(many=True)},
    tags=["Listings"],
)
class FavoriteListView(generics.ListAPIView):
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).order_by("-created_at")


@extend_schema_view(
    list=extend_schema(summary="Reels ro'yxati", tags=["Reels"]),
    retrieve=extend_schema(summary="Reel tafsilotlari", tags=["Reels"]),
    create=extend_schema(summary="Yangi reel yuklash", tags=["Reels"]),
    update=extend_schema(summary="Reelni yangilash", tags=["Reels"]),
    partial_update=extend_schema(summary="Reelni qisman yangilash", tags=["Reels"]),
    destroy=extend_schema(summary="Reelni o'chirish", tags=["Reels"]),
    view=extend_schema(
        summary="Reel ko'rishlar sonini oshirish",
        request=None,
        responses={200: OpenApiResponse(description="Ko'rishlar soni oshirildi")},
        tags=["Reels"],
    ),
)
class ReelViewSet(ModelViewSet):
    queryset = Reel.objects.all().order_by("-created_at")
    serializer_class = ReelSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[])
    def view(self, request, pk=None):
        reel = self.get_object()
        reel.view_count += 1
        reel.save()
        return Response({"status": "view counted"})


@extend_schema(
    summary="Foydalanuvchi yoki e'lon haqida shikoyat yuborish",
    request=ReportSerializer,
    responses={
        201: ReportSerializer,
        400: OpenApiResponse(description="target_user yoki target_listing dan kamida bittasi berilishi shart"),
    },
    tags=["Reports"],
)
class ReportCreateView(generics.CreateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
