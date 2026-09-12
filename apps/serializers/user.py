from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, Serializer

from apps.models import User


class RequestOTPSerializer(Serializer):
    phone = CharField(max_length=15)
    full_name = CharField(max_length=255, required=False)


class VerifyOTPSerializer(Serializer):
    phone = CharField(max_length=15)
    code = CharField(max_length=6)


class UserPublicSerializer(ModelSerializer):
    avatar_url = SerializerMethodField()
    posts_count = SerializerMethodField()
    followers_count = SerializerMethodField()
    rating = SerializerMethodField()
    rating_count = SerializerMethodField()
    tier_id = SerializerMethodField()
    tier_name = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "phone", "full_name", "avatar_url", "role", "is_verified",
            "bio", "created_at", "followers_count", "posts_count",
            "rating", "rating_count", "tier_id", "tier_name",
        )

    def get_avatar_url(self, obj):
        request = self.context.get("request")
        if not obj.avatar:
            return None
        url = obj.avatar.url
        return request.build_absolute_uri(url) if request else url

    def get_posts_count(self, obj):
        return obj.listings.count()

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_rating(self, obj):
        return 0.0  # TODO: haqiqiy baholash tizimi keyingi bosqichda qo'shiladi

    def get_rating_count(self, obj):
        return 0  # TODO: haqiqiy baholash tizimi keyingi bosqichda qo'shiladi

    def get_tier_id(self, obj):
        plan = obj.current_plan
        return plan.slug if plan else None

    def get_tier_name(self, obj):
        plan = obj.current_plan
        return plan.name if plan else None


class MeSerializer(ModelSerializer):
    avatar_url = SerializerMethodField()
    posts_count = SerializerMethodField()
    followers_count = SerializerMethodField()
    following_count = SerializerMethodField()
    rating = SerializerMethodField()
    rating_count = SerializerMethodField()
    tier_id = SerializerMethodField()
    tier_name = SerializerMethodField()
    plan_expires_at = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "phone", "full_name", "bio", "avatar", "avatar_url",
            "is_verified", "is_vip", "role", "language", "dark_mode",
            "created_at", "followers_count", "following_count", "posts_count",
            "rating", "rating_count", "tier_id", "tier_name", "plan_expires_at",
        )
        read_only_fields = ("phone", "is_verified", "is_vip", "role", "created_at")

    def get_avatar_url(self, obj):
        request = self.context.get("request")
        if not obj.avatar:
            return None
        url = obj.avatar.url
        return request.build_absolute_uri(url) if request else url

    def get_posts_count(self, obj):
        return obj.listings.count()

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_rating(self, obj):
        return 0.0

    def get_rating_count(self, obj):
        return 0

    def get_tier_id(self, obj):
        plan = obj.current_plan
        return plan.slug if plan else None

    def get_tier_name(self, obj):
        plan = obj.current_plan
        return plan.name if plan else None

    def get_plan_expires_at(self, obj):
        sub = obj.active_subscription
        return sub.expires_at if sub else None
