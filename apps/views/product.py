from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.models import Listing, Report
from apps.permission import IsOwnerOrReadOnly, IsVerifiedUser
from apps.serializers.product import (
    ProductCreateSerializer,
    ProductReportSerializer,
    ProductSerializer,
)
from apps.utils.exceptions import RelistCooldownError


@extend_schema_view(
    list=extend_schema(summary="Ochiq e'lonlar lentasi", tags=["Products"]),
    retrieve=extend_schema(summary="Bitta e'lonni olish", tags=["Products"]),
    create=extend_schema(summary="Yangi e'lon joylash", tags=["Products"]),
    update=extend_schema(summary="E'lonni tahrirlash", tags=["Products"]),
    partial_update=extend_schema(summary="E'lonni qisman tahrirlash", tags=["Products"]),
    destroy=extend_schema(summary="E'lonni o'chirish", tags=["Products"]),
    mine=extend_schema(summary="O'zining barcha e'lonlari", tags=["Products"]),
    relist=extend_schema(summary="E'lonni qayta ko'tarish", tags=["Products"]),
    report=extend_schema(summary="E'lonni shikoyat qilish", tags=["Products"]),
)
class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProductCreateSerializer
        return ProductSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsVerifiedUser()]
        if self.action in ("mine", "relist", "report"):
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        if self.action == "mine":
            return Listing.objects.filter(user=self.request.user)
        return Listing.objects.filter(status="active")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != "active" and (
            not request.user.is_authenticated or instance.user != request.user
        ):
            from rest_framework.exceptions import NotFound

            raise NotFound()
        return super().retrieve(request, *args, **kwargs)

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
        else:
            expires_days = 30

        serializer.save(status="pending", expires_at=timezone.now() + timedelta(days=expires_days))

    @action(detail=False, methods=["get"])
    def mine(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = ProductSerializer(page or queryset, many=True, context={"request": request})
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def relist(self, request, pk=None):
        listing = self.get_object()
        if listing.user != request.user:
            raise PermissionDenied("Faqat egasi qayta ko'tarishi mumkin.")

        plan = request.user.current_plan
        cooldown_days = plan.reboost_interval_days if plan else 3
        reference_time = listing.relisted_at or listing.created_at
        earliest_allowed = reference_time + timedelta(days=cooldown_days)

        if timezone.now() < earliest_allowed:
            raise RelistCooldownError()

        listing.relisted_at = timezone.now()
        listing.save(update_fields=["relisted_at"])
        return Response(status=204)

    @action(detail=True, methods=["post"])
    def report(self, request, pk=None):
        listing = self.get_object()
        serializer = ProductReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reason_codes = serializer.validated_data["reason_codes"]
        message = serializer.validated_data.get("message", "")
        
        reason_choices = dict(Report._meta.get_field("reason").choices)
        first_reason = reason_codes[0] if reason_codes else "other"
        reason = first_reason if first_reason in reason_choices else "other"

        Report.objects.get_or_create(
            reporter=request.user,
            target_listing=listing,
            defaults={"reason": reason, "comment": message or ", ".join(reason_codes)},
        )
        return Response(status=204)
