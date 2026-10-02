from datetime import timedelta

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Case, IntegerField, Value, When
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
from rest_framework.exceptions import NotFound, ValidationError
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
        parameters=[
            OpenApiParameter("category", OpenApiTypes.UUID, OpenApiParameter.QUERY, description="Kategoriya ID"),
            OpenApiParameter("min_price", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="Minimal narx"),
            OpenApiParameter("max_price", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="Maksimal narx"),
            OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Saralash: price, -price, created_at, -created_at, distance"),
            OpenApiParameter("lat", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="Kenglik (masofa bo'yicha saralash uchun)"),
            OpenApiParameter("lng", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="Uzunlik (masofa bo'yicha saralash uchun)"),
        ],
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
        summary="Xaritada e'lonlarni ko'rish (radius yoki bounding box bo'yicha)",
        parameters=[
            OpenApiParameter("lat", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="Markaziy nuqta kengligi"),
            OpenApiParameter("lng", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="Markaziy nuqta uzunligi"),
            OpenApiParameter("radius_km", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="Radius (km), standart 10"),
            OpenApiParameter("min_lat", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="Bounding box min kenglik"),
            OpenApiParameter("max_lat", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="Bounding box max kenglik"),
            OpenApiParameter("min_lng", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="Bounding box min uzunlik"),
            OpenApiParameter("max_lng", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, description="Bounding box max uzunlik"),
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
            queryset = Listing.objects.filter(status="active")
            params = self.request.query_params

            category = params.get("category")
            if category:
                queryset = queryset.filter(category_id=category)

            min_price = params.get("min_price")
            if min_price:
                try:
                    queryset = queryset.filter(price__gte=float(min_price))
                except ValueError:
                    raise ValidationError({"min_price": "Noto'g'ri son formati."})

            max_price = params.get("max_price")
            if max_price:
                try:
                    queryset = queryset.filter(price__lte=float(max_price))
                except ValueError:
                    raise ValidationError({"max_price": "Noto'g'ri son formati."})

            queryset = queryset.annotate(
                type_rank=Case(
                    When(listing_type="top", then=Value(0)),
                    When(listing_type="vip", then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                )
            )

            ordering = params.get("ordering")
            allowed_orderings = {"price", "-price", "created_at", "-created_at"}

            lat = params.get("lat")
            lng = params.get("lng")
            if lat and lng:
                try:
                    lat_val, lng_val = float(lat), float(lng)
                    center = Point(lng_val, lat_val, srid=4326)
                    queryset = queryset.annotate(distance=Distance("location", center))
                    allowed_orderings.add("distance")
                except ValueError:
                    raise ValidationError({"lat": "lat/lng noto'g'ri formatda."})
            elif ordering == "distance":
                raise ValidationError("Masofa bo'yicha saralash uchun lat va lng berilishi shart.")

            secondary_ordering = ordering if ordering in allowed_orderings else "-created_at"

            return queryset.order_by("type_rank", secondary_ordering)

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
        user = self.request.user
        plan = user.current_plan

        if plan:
            active_count = Listing.objects.filter(
                user=user, status__in=["pending", "active"]
            ).count()
            if active_count >= plan.max_active_listings:
                raise ValidationError(
                    f"Tarifingiz bo'yicha maksimal {plan.max_active_listings} ta "
                    "aktiv e'lon joylashtirish mumkin."
                )

            month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_count = Listing.objects.filter(user=user, created_at__gte=month_start).count()
            if monthly_count >= plan.max_monthly_new_listings:
                raise ValidationError(
                    f"Tarifingiz bo'yicha oyiga maksimal {plan.max_monthly_new_listings} "
                    "ta yangi e'lon joylashtirish mumkin."
                )

            expires_days = plan.listing_duration_days
            listing_type = plan.auto_listing_type
        else:
            expires_days = 30
            listing_type = "normal"

        serializer.save(
            user=user,
            status="pending",
            listing_type=listing_type,
            expires_at=timezone.now() + timedelta(days=expires_days),
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
        queryset = Listing.objects.filter(status="active")

        min_lat = request.query_params.get("min_lat")
        max_lat = request.query_params.get("max_lat")
        min_lng = request.query_params.get("min_lng")
        max_lng = request.query_params.get("max_lng")

        if min_lat and max_lat and min_lng and max_lng:
            try:
                min_lat, max_lat = float(min_lat), float(max_lat)
                min_lng, max_lng = float(min_lng), float(max_lng)
            except ValueError:
                raise ValidationError("Bounding box koordinatalari noto'g'ri formatda.")
            queryset = queryset.filter(
                lat__gte=min_lat, lat__lte=max_lat,
                lng__gte=min_lng, lng__lte=max_lng,
            )
        else:
            lat = request.query_params.get("lat")
            lng = request.query_params.get("lng")
            try:
                radius_km = float(request.query_params.get("radius_km", 10))
            except ValueError:
                raise ValidationError("radius_km noto'g'ri formatda.")

            if lat and lng:
                try:
                    lat, lng = float(lat), float(lng)
                except ValueError:
                    raise ValidationError("lat/lng noto'g'ri formatda.")
                center = Point(lng, lat, srid=4326)
                queryset = queryset.filter(
                    location__distance_lte=(center, D(km=radius_km))
                ).annotate(distance=Distance("location", center)).order_by("distance")

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
