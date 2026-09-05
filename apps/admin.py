from django.contrib import admin

from apps.models import Plan, Subscription, User


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "billing_period_days", "max_active_listings", "sort_order")
    ordering = ("sort_order",)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "started_at", "expires_at", "is_active")
    list_filter = ("plan", "is_active")
    search_fields = ("user__phone", "user__full_name")
    autocomplete_fields = ["user"]

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("phone", "full_name", "role", "is_staff")
    search_fields = ("phone", "full_name")
