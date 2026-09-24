import pytest
from django.urls import reverse

from apps.models import Plan, PromoCode, Subscription


@pytest.mark.django_db
def test_free_listing_grants_promo_code(auth_client, verified_user, category):
    plan = Plan.objects.create(
        name="Free", slug="free_promo", price=0, billing_period_days=30,
        max_active_listings=10, max_monthly_new_listings=10,
        max_photos_per_listing=6, max_videos_per_listing=1,
        listing_duration_days=30, reboost_interval_days=3, auto_listing_type="normal",
    )
    Subscription.objects.create(user=verified_user, plan=plan)
    auth_client.force_authenticate(user=verified_user)

    response = auth_client.post(reverse('product-list'), {
        "category_id": category.id, "title": "Bepul", "description": "D",
        "cost": 0, "address": "A", "lat": 0, "lng": 0,
    })

    assert response.status_code == 201
    assert PromoCode.objects.filter(user=verified_user).exists()

@pytest.mark.django_db
def test_paid_listing_does_not_grant_promo_code(auth_client, verified_user, category):
    plan = Plan.objects.create(
        name="Free", slug="free_promo2", price=0, billing_period_days=30,
        max_active_listings=10, max_monthly_new_listings=10,
        max_photos_per_listing=6, max_videos_per_listing=1,
        listing_duration_days=30, reboost_interval_days=3, auto_listing_type="normal",
    )
    Subscription.objects.create(user=verified_user, plan=plan)
    auth_client.force_authenticate(user=verified_user)

    response = auth_client.post(reverse('product-list'), {
        "category_id": category.id, "title": "Pullik", "description": "D",
        "cost": 1000, "address": "A", "lat": 0, "lng": 0,
    })

    assert response.status_code == 201
    assert not PromoCode.objects.filter(user=verified_user).exists()

@pytest.mark.django_db
def test_promo_codes_mine_list(auth_client, verified_user):
    PromoCode.objects.create(
        user=verified_user, code="ABC12345", reward="free_top_placement",
    )
    auth_client.force_authenticate(user=verified_user)

    response = auth_client.get(reverse('promo-code-mine'))

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["code"] == "ABC12345"

@pytest.mark.django_db
def test_promo_code_check_not_found(auth_client, verified_user):
    auth_client.force_authenticate(user=verified_user)

    response = auth_client.get(reverse('promo-code-check', kwargs={'code': 'NOPE0000'}))

    assert response.status_code == 404

@pytest.mark.django_db
def test_promo_code_check_belongs_to_other(auth_client, verified_user, other_user):
    PromoCode.objects.create(user=other_user, code="OTHR0001", reward="free_top_placement")
    auth_client.force_authenticate(user=verified_user)

    response = auth_client.get(reverse('promo-code-check', kwargs={'code': 'OTHR0001'}))

    assert response.status_code == 403

@pytest.mark.django_db
def test_promo_code_check_already_used(auth_client, verified_user):
    PromoCode.objects.create(
        user=verified_user, code="USED0001", reward="free_top_placement", used=True,
    )
    auth_client.force_authenticate(user=verified_user)

    response = auth_client.get(reverse('promo-code-check', kwargs={'code': 'USED0001'}))

    assert response.status_code == 400

@pytest.mark.django_db
def test_create_listing_with_promo_code_sets_top_and_marks_used(auth_client, verified_user, category):
    plan = Plan.objects.create(
        name="Free", slug="free_promo3", price=0, billing_period_days=30,
        max_active_listings=10, max_monthly_new_listings=10,
        max_photos_per_listing=6, max_videos_per_listing=1,
        listing_duration_days=30, reboost_interval_days=3, auto_listing_type="normal",
    )
    Subscription.objects.create(user=verified_user, plan=plan)
    promo = PromoCode.objects.create(
        user=verified_user, code="TOPFREE1", reward="free_top_placement",
    )
    auth_client.force_authenticate(user=verified_user)

    response = auth_client.post(reverse('product-list'), {
        "category_id": category.id, "title": "TOP sinov", "description": "D",
        "cost": 500, "address": "A", "lat": 0, "lng": 0, "promo_code": "TOPFREE1",
    })

    assert response.status_code == 201
    from apps.models import Listing
    listing = Listing.objects.get(id=response.data['id'])
    assert listing.listing_type == "top"
    promo.refresh_from_db()
    assert promo.used is True
