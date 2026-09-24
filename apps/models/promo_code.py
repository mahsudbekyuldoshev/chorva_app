from django.conf import settings
from django.db import models

from apps.models.base import BaseModel


class PromoCode(BaseModel):
    class Reward(models.TextChoices):
        FREE_TOP_PLACEMENT = "free_top_placement", "Bepul TOP joylashtirish"
        TOP_DISCOUNT = "top_discount", "TOP chegirmasi"

    code = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="promo_codes", on_delete=models.CASCADE
    )
    reward = models.CharField(max_length=30, choices=Reward.choices)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.code
