import pytest
from django.urls import reverse
from django.utils import timezone

from apps.models import Listing, Plan, Subscription, User


@pytest.mark.django_db
def test_plan_list_is_public(api_client):
    Plan.objects.create(
        name="Free", slug="free", price=0, billing_period_days=30,
        max_active_listings=3, max_monthly_new_listings=2,
        max_photos_per_listing=6, max_videos_per_listing=1,
        listing_duration_days=30, reboost_interval_days=3,
    )
    response = api_client.get(reverse('plan-list'))
    assert response.status_code == 200
    assert len(response.data) == 1

@pytest.mark.django_db
def test_new_user_gets_free_subscription(api_client):
    Plan.objects.create(
        name="Free", slug="free", price=0, billing_period_days=30,
        max_active_listings=3, max_monthly_new_listings=2,
        max_photos_per_listing=6, max_videos_per_listing=1,
        listing_duration_days=30, reboost_interval_days=3,
    )
    from django.core.cache import cache
    cache.set("otp_+998901112233", "1234", timeout=120)
    response = api_client.post(reverse('verify-otp'), {"phone": "+998901112233", "code": "1234"})
    assert response.status_code == 200
    user = User.objects.get(phone="+998901112233")
    assert user.current_plan is not None
    assert user.current_plan.slug == "free"

@pytest.mark.django_db
def test_listing_creation_blocked_by_active_limit(auth_client, verified_user, category):
    plan = Plan.objects.create(
        name="Free", slug="free", price=0, billing_period_days=30,
        max_active_listings=1, max_monthly_new_listings=10,
        max_photos_per_listing=6, max_videos_per_listing=1,
        listing_duration_days=30, reboost_interval_days=3,
    )
    Subscription.objects.create(user=verified_user, plan=plan)
    Listing.objects.create(
        user=verified_user, category=category, title="Birinchi", description="D",
        price=100, lat=0, lng=0, address_text="A", status="active",
        expires_at=timezone.now(),
    )
    # Re-authenticate with verified user
    auth_client.force_authenticate(user=verified_user)
    response = auth_client.post(reverse('listing-list'), {
        "category": category.id, "title": "Ikkinchi", "description": "D", "price": 100,
    })
    assert response.status_code == 400
