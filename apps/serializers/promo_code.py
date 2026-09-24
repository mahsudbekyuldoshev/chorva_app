from rest_framework import serializers

from apps.models import PromoCode


class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = ("code", "used", "reward", "discount_amount")


class PromoCodeCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = ("discount_amount", "reward")
