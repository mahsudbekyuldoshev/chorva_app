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
        )
        read_only_fields = ("phone", "is_verified", "is_vip")
