from datetime import timedelta
from math import asin, cos, radians, sin, sqrt

from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiParameter,
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

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all().order_by("sort_order")
    serializer_class = CategorySerializer
    permission_classes = []

@extend_schema_view(
    list=extend_schema(summary="E'lonlar ro'yxatini olish", tags=["Listings"]),
    retrieve=extend_schema(summary="E'lon tafsilotlarini olish", tags=["Listings"]),
    create=extend_schema(summary="Yangi e'lon yaratish", tags=["Listings"]),
    update=extend_schema(summary="E'lonni yangilash", tags=["Listings"]),
    partial_update=extend_schema(summary="E'lonni qisman yangilash", tags=["Listings"]),
    destroy=extend_schema(summary="E'lonni o'chirish", tags=["Listings"]),
    favorite=extend_schema(summary="E'lonni sevimlilarga qo'shish/o'chirish", tags=["Listings"]),
    map=extend_schema(
        summary="Xaritada e'lonlarni ko'rish",
        tags=["Listings"],
        parameters=[
            OpenApiParameter("lat", OpenApiTypes.FLOAT, OpenApiParameter.QUERY),
            OpenApiParameter("lng", OpenApiTypes.FLOAT, OpenApiParameter.QUERY),
            OpenApiParameter("radius_km", OpenApiTypes.FLOAT, OpenApiParameter.QUERY),
        ],
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



class FavoriteListView(generics.ListAPIView):
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).order_by("-created_at")


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


class ReportCreateView(generics.CreateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
