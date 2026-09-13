from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.models import Listing


@pytest.mark.django_db
def test_product_list_shape(api_client, verified_user, category):
    Listing.objects.create(
        user=verified_user, category=category, title="Test", description="D",
        price=0, lat=1.0, lng=2.0, address_text="Toshkent", status="active",
        listing_type="top", is_negotiable=True, has_delivery=True,
        phone="+998900000000", expires_at=timezone.now() + timedelta(days=30),
    )

    response = api_client.get(reverse('product-list'))

    assert response.status_code == 200
    item = response.data[0]
    assert float(item["cost"]) == 0.0
    assert item["is_free"] is True
    assert item["is_top"] is True
    assert item["is_negotiable"] is True
    assert item["has_delivery"] is True
    assert item["status"] == "approved"
    assert item["address"] == "Toshkent"
    assert "owner" in item and item["owner"]["phone"] == verified_user.phone

@pytest.mark.django_db
def test_product_status_mapping(api_client, verified_user, category):
    statuses = {"pending": "pending", "active": "approved",
                "rejected": "rejected", "expired": "removed", "sold": "removed"}
    for internal, external in statuses.items():
        Listing.objects.create(
            user=verified_user, category=category, title=internal, description="D",
            price=100, lat=0, lng=0, address_text="A", status=internal,
            expires_at=timezone.now() + timedelta(days=30),
        )

    api_client.force_authenticate(user=verified_user)
    response = api_client.get(reverse('product-mine'))

    assert response.status_code == 200
    by_title = {item["title"]: item["status"] for item in response.data}
    for internal, external in statuses.items():
        assert by_title[internal] == external

@pytest.mark.django_db
def test_create_product_with_is_top_free(auth_client, verified_user, category):
    auth_client.force_authenticate(user=verified_user)

    response = auth_client.post(reverse('product-list'), {
        "category_id": category.id, "title": "VIP sinov", "description": "D",
        "cost": 1000, "address": "A", "lat": 0, "lng": 0, "is_top": True,
    })

    assert response.status_code == 201
    listing = Listing.objects.get(id=response.data['id'])
    assert listing.listing_type == "top"

@pytest.mark.django_db
def test_relist_cooldown_blocks(auth_client, verified_user, category):
    listing = Listing.objects.create(
        user=verified_user, category=category, title="Test", description="D",
        price=100, lat=0, lng=0, address_text="A", status="active",
        expires_at=timezone.now() + timedelta(days=30),
        relisted_at=timezone.now(),
    )
    auth_client.force_authenticate(user=verified_user)

    response = auth_client.post(reverse('product-relist', kwargs={'pk': listing.id}))

    assert response.status_code == 400

@pytest.mark.django_db
def test_relist_succeeds_after_cooldown(auth_client, verified_user, category):
    listing = Listing.objects.create(
        user=verified_user, category=category, title="Test", description="D",
        price=100, lat=0, lng=0, address_text="A", status="active",
        expires_at=timezone.now() + timedelta(days=30),
        relisted_at=timezone.now() - timedelta(days=10),
    )
    auth_client.force_authenticate(user=verified_user)

    response = auth_client.post(reverse('product-relist', kwargs={'pk': listing.id}))

    assert response.status_code == 204
    listing.refresh_from_db()
    assert (timezone.now() - listing.relisted_at).total_seconds() < 5

@pytest.mark.django_db
def test_product_report_dedupes(auth_client, verified_user, other_user, category):
    listing = Listing.objects.create(
        user=other_user, category=category, title="Test", description="D",
        price=100, lat=0, lng=0, address_text="A", status="active",
        expires_at=timezone.now() + timedelta(days=30),
    )
    auth_client.force_authenticate(user=verified_user)

    first = auth_client.post(reverse('product-report', kwargs={'pk': listing.id}),
                              {"reason_codes": ["spam"], "message": "test"})
    second = auth_client.post(reverse('product-report', kwargs={'pk': listing.id}),
                               {"reason_codes": ["spam"], "message": "test again"})

    assert first.status_code == 204
    assert second.status_code == 204
    from apps.models import Report
    assert Report.objects.filter(reporter=verified_user, target_listing=listing).count() == 1
