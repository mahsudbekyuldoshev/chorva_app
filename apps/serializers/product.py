from rest_framework import serializers

from apps.models import Category, Listing
from apps.utils.media import (
    MAX_VIDEO_DURATION_SECONDS,
    MAX_VIDEO_SIZE_MB,
    VideoProcessingError,
    generate_thumbnail_file,
    get_video_duration_seconds,
)

STATUS_MAP = {
    "pending": "pending",
    "active": "approved",
    "rejected": "rejected",
    "expired": "removed",
    "sold": "removed",
}


class ProductOwnerSerializer(serializers.Serializer):
    phone = serializers.CharField()
    full_name = serializers.CharField()
    avatar_url = serializers.SerializerMethodField()
    is_verified = serializers.BooleanField()

    def get_avatar_url(self, obj):
        request = self.context.get("request")
        if not obj.avatar:
            return None
        url = obj.avatar.url
        return request.build_absolute_uri(url) if request else url


class ProductSerializer(serializers.ModelSerializer):
    cost = serializers.DecimalField(source="price", max_digits=14, decimal_places=2)
    address = serializers.CharField(source="address_text")
    category_id = serializers.CharField()
    is_free = serializers.SerializerMethodField()
    is_top = serializers.SerializerMethodField()
    is_vip = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    reel_video = serializers.SerializerMethodField()
    reel_thumbnail = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = (
            "id", "title", "description", "cost", "currency", "is_free",
            "is_top", "is_vip", "is_negotiable", "has_delivery",
            "phone", "additional_phone", "address", "lat", "lng",
            "images", "reel_video", "reel_thumbnail", "category_id",
            "status", "created_at", "relisted_at", "view_count", "owner",
        )

    def get_is_free(self, obj):
        return obj.price == 0

    def get_is_top(self, obj):
        return obj.listing_type == "top"

    def get_is_vip(self, obj):
        return obj.listing_type == "vip"

    def get_status(self, obj):
        return STATUS_MAP.get(obj.status, "removed")

    def _abs_url(self, file_field):
        if not file_field:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(file_field.url) if request else file_field.url

    def get_images(self, obj):
        return [self._abs_url(m.file) for m in obj.media.filter(media_type="image")]

    def get_reel_video(self, obj):
        return self._abs_url(obj.reel_video)

    def get_reel_thumbnail(self, obj):
        return self._abs_url(obj.reel_thumbnail)

    def get_owner(self, obj):
        return ProductOwnerSerializer(obj.user, context=self.context).data


class ProductCreateSerializer(serializers.ModelSerializer):
    cost = serializers.DecimalField(source="price", max_digits=14, decimal_places=2)
    address = serializers.CharField(source="address_text")
    category_id = serializers.PrimaryKeyRelatedField(source="category", queryset=Category.objects.all())
    is_top = serializers.BooleanField(required=False, default=False, write_only=True)
    is_vip = serializers.BooleanField(required=False, default=False, write_only=True)
    is_free = serializers.BooleanField(required=False, default=False, write_only=True)
    promo_code = serializers.CharField(required=False, allow_null=True, allow_blank=True, write_only=True)
    images = serializers.ListField(child=serializers.FileField(), required=False, write_only=True)
    reel_video = serializers.FileField(required=False, allow_null=True)
    reel_thumbnail = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Listing
        fields = (
            "id", "category_id", "title", "description", "cost", "is_free",
            "is_top", "is_vip", "is_negotiable", "has_delivery", "phone",
            "additional_phone", "address", "lat", "lng", "promo_code",
            "images", "reel_video", "reel_thumbnail",
        )

    def validate_reel_video(self, value):
        if not value:
            return value
        size_mb = value.size / (1024 * 1024)
        if size_mb > MAX_VIDEO_SIZE_MB:
            raise serializers.ValidationError(
                f"Video hajmi {MAX_VIDEO_SIZE_MB}MB dan oshmasligi kerak."
            )
        try:
            duration = get_video_duration_seconds(value)
        except VideoProcessingError:
            raise serializers.ValidationError(
                "Video faylni tahlil qilib bo'lmadi — fayl buzilgan bo'lishi mumkin."
            )
        if duration > MAX_VIDEO_DURATION_SECONDS:
            raise serializers.ValidationError(
                f"Video davomiyligi {MAX_VIDEO_DURATION_SECONDS} soniyadan oshmasligi kerak."
            )
        return value

    def validate_promo_code(self, value):
        if not value:
            return value
        from apps.models import PromoCode
        request = self.context["request"]
        promo = PromoCode.objects.filter(code=value, user=request.user, used=False).first()
        if not promo:
            raise serializers.ValidationError(
                "Promo kod topilmadi, sizga tegishli emas yoki allaqachon ishlatilgan."
            )
        return value

    def create(self, validated_data):
        images = validated_data.pop("images", [])
        is_top = validated_data.pop("is_top", False)
        is_vip = validated_data.pop("is_vip", False)
        validated_data.pop("is_free", None)
        promo_code = validated_data.pop("promo_code", None)

        if is_top:
            validated_data["listing_type"] = "top"
        elif is_vip:
            validated_data["listing_type"] = "vip"
        else:
            validated_data.setdefault("listing_type", "normal")

        request = self.context["request"]
        if not validated_data.get("phone"):
            validated_data["phone"] = request.user.phone

        from apps.models import ListingMedia
        listing = Listing.objects.create(user=request.user, **validated_data)

        for index, image in enumerate(images):
            ListingMedia.objects.create(
                listing=listing, file=image, media_type="image", sort_order=index
            )

        if listing.reel_video and not listing.reel_thumbnail:
            try:
                thumb = generate_thumbnail_file(listing.reel_video)
                listing.reel_thumbnail.save(thumb.name, thumb, save=True)
            except VideoProcessingError:
                pass

        if promo_code:
            from django.utils import timezone

            from apps.models import PromoCode
            promo = PromoCode.objects.get(code=promo_code, user=request.user, used=False)
            if promo.reward == PromoCode.Reward.FREE_TOP_PLACEMENT:
                listing.listing_type = "top"
                listing.save(update_fields=["listing_type"])
            promo.used = True
            promo.used_at = timezone.now()
            promo.save(update_fields=["used", "used_at"])

        return listing


class ProductReportSerializer(serializers.Serializer):
    reason_codes = serializers.ListField(child=serializers.CharField(), required=True)
    message = serializers.CharField(required=False, allow_blank=True)
