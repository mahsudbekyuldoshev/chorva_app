from math import asin, cos, radians, sin, sqrt

from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.models import Category, Favorite, Listing, Reel, Report
from apps.permission import IsOwnerOrReadOnly
from apps.serializers import (
    CategorySerializer,
    FavoriteSerializer,
    ListingCreateSerializer,
    ListingDetailSerializer,
    ListingListSerializer,
    ReelSerializer,
    ReportSerializer,
)


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles
    return c * r


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all().order_by("sort_order")
    serializer_class = CategorySerializer
    permission_classes = []


class ListingViewSet(ModelViewSet):
    queryset = Listing.objects.filter(status="active").order_by("-created_at")
    permission_classes = [IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return ListingListSerializer
        if self.action == "retrieve":
            return ListingDetailSerializer
        if self.action in ["create", "update", "partial_update"]:
            return ListingCreateSerializer
        return ListingListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status="pending")

    @action(detail=True, methods=["post", "delete"], permission_classes=[])
    def favorite(self, request, pk=None):
        listing = self.get_object()
        if request.method == "POST":
            favorite, created = Favorite.objects.get_or_create(
                user=request.user, listing=listing
            )
            return Response(
                {"status": "added to favorites"}, status=status.HTTP_201_CREATED
            )
        else:
            Favorite.objects.filter(user=request.user, listing=listing).delete()
            return Response(
                {"status": "removed from favorites"}, status=status.HTTP_204_NO_CONTENT
            )

    @action(detail=False, methods=["get"], permission_classes=[])
    def map(self, request):
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        radius = request.query_params.get("radius_km", 10)

        queryset = self.get_queryset()

        if lat and lng:
            lat = float(lat)
            lng = float(lng)
            radius = float(radius)

            # Temporary Haversine filter in Python (inefficient for large datasets, but works for now)
            # PostGIS would do this much better
            all_listings = list(queryset)
            filtered_ids = []
            for item in all_listings:
                dist = haversine(lng, lat, item.lng, item.lat)
                if dist <= radius:
                    filtered_ids.append(item.id)
            queryset = queryset.filter(id__in=filtered_ids)

        serializer = ListingListSerializer(
            queryset, many=True, context={"request": request}
        )
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
