from django.conf import settings
from django.db.models.deletion import CASCADE, PROTECT
from django.db.models.fields import (
    BooleanField,
    CharField,
    DateTimeField,
    DecimalField,
    PositiveIntegerField,
    SlugField,
)
from django.db.models.fields.related import ForeignKey

from apps.models.base import BaseModel


class Plan(BaseModel):
    name = CharField(max_length=50, unique=True)
    slug = SlugField(max_length=50, unique=True)
    price = DecimalField(max_digits=12, decimal_places=2, default=0)
    original_price = DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    billing_period_days = PositiveIntegerField(help_text="To'lov davri kunlarda (masalan 30 yoki 365)")

    max_active_listings = PositiveIntegerField()
    max_monthly_new_listings = PositiveIntegerField()
    max_photos_per_listing = PositiveIntegerField()
    max_videos_per_listing = PositiveIntegerField()
    listing_duration_days = PositiveIntegerField()

    has_view_stats = BooleanField(default=False)
    has_contact_stats = BooleanField(default=False)
    reboost_interval_days = PositiveIntegerField(help_text="Qayta ko'tarish oralig'i (kun)")
    free_top_vip = BooleanField(default=False, help_text="TOP/VIP joylashtirish bepul kiritilganmi")
    badge = CharField(max_length=50, blank=True)
    sort_order = PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return self.name


class Subscription(BaseModel):
    user = ForeignKey(settings.AUTH_USER_MODEL, related_name="subscriptions", on_delete=CASCADE)
    plan = ForeignKey(Plan, related_name="subscriptions", on_delete=PROTECT)
    started_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField(null=True, blank=True, help_text="Free reja uchun bo'sh (muddatsiz)")
    is_active = BooleanField(default=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user} — {self.plan}"
