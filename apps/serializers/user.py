from rest_framework import serializers
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer, Serializer

from apps.models import User


class RequestOTPSerializer(Serializer):
    phone = CharField(max_length=15)
    full_name = CharField(max_length=255, required=False)


class VerifyOTPSerializer(Serializer):
    phone = CharField(max_length=15)
    code = CharField(max_length=4)


class UserPublicSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "full_name", "avatar", "is_verified", "is_vip")


class MeSerializer(ModelSerializer):
    current_plan = serializers.SerializerMethodField()
    plan_expires_at = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "phone",
            "full_name",
            "avatar",
            "is_verified",
            "is_vip",
            "language",
            "dark_mode",
            "role",
            "current_plan",
            "plan_expires_at",
        )
        read_only_fields = ("phone", "is_verified", "is_vip", "role")

    def get_current_plan(self, obj):
        plan = obj.current_plan
        return plan.name if plan else None

    def get_plan_expires_at(self, obj):
        sub = obj.active_subscription
        return sub.expires_at if sub else None
