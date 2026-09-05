from django.core.management.base import BaseCommand

from apps.models import Plan

PLANS = [
    {"name": "Free", "slug": "free", "price": 0, "original_price": None,
     "billing_period_days": 30, "max_active_listings": 3, "max_monthly_new_listings": 2,
     "max_photos_per_listing": 6, "max_videos_per_listing": 1, "listing_duration_days": 30,
     "has_view_stats": False, "has_contact_stats": False, "reboost_interval_days": 3,
     "free_top_vip": False, "badge": "", "sort_order": 1},
    {"name": "Haftalik", "slug": "weekly", "price": 15000, "original_price": None,
     "billing_period_days": 30, "max_active_listings": 5, "max_monthly_new_listings": 8,
     "max_photos_per_listing": 6, "max_videos_per_listing": 1, "listing_duration_days": 30,
     "has_view_stats": False, "has_contact_stats": False, "reboost_interval_days": 3,
     "free_top_vip": False, "badge": "", "sort_order": 2},
    {"name": "Pro", "slug": "pro", "price": 49000, "original_price": 70000,
     "billing_period_days": 30, "max_active_listings": 15, "max_monthly_new_listings": 30,
     "max_photos_per_listing": 8, "max_videos_per_listing": 2, "listing_duration_days": 45,
     "has_view_stats": True, "has_contact_stats": False, "reboost_interval_days": 1,
     "free_top_vip": True, "badge": "Pro belgisi", "sort_order": 3},
    {"name": "Business", "slug": "business", "price": 149000, "original_price": 199000,
     "billing_period_days": 30, "max_active_listings": 100, "max_monthly_new_listings": 200,
     "max_photos_per_listing": 10, "max_videos_per_listing": 3, "listing_duration_days": 60,
     "has_view_stats": True, "has_contact_stats": True, "reboost_interval_days": 1,
     "free_top_vip": True, "badge": "Business belgisi", "sort_order": 4},
    {"name": "Business Pro", "slug": "business_pro", "price": 599000, "original_price": 1000000,
     "billing_period_days": 365, "max_active_listings": 250, "max_monthly_new_listings": 500,
     "max_photos_per_listing": 12, "max_videos_per_listing": 5, "listing_duration_days": 90,
     "has_view_stats": True, "has_contact_stats": True, "reboost_interval_days": 1,
     "free_top_vip": True, "badge": "Business Pro belgisi", "sort_order": 5},
]

class Command(BaseCommand):
    help = "Tarif rejalarini (Free/Haftalik/Pro/Business/Business Pro) yuklaydi."

    def handle(self, *args, **options):
        created = 0
        for data in PLANS:
            _, was_created = Plan.objects.get_or_create(slug=data["slug"], defaults=data)
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Tayyor. {created} ta yangi reja qo'shildi."))
