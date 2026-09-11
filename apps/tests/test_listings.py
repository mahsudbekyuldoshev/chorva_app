from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.models import Favorite, Listing, Plan, Subscription


def _fake_image(name="photo.jpg"):
    return SimpleUploadedFile(name, b"fake-image-content", content_type="image/jpeg")

def _fake_video(name="video.mp4"):
    return SimpleUploadedFile(name, b"fake-video-content", content_type="video/mp4")


@pytest.mark.django_db
def test_unverified_user_cannot_create_listing(api_client, user, category):
    api_client.force_authenticate(user=user)
    data = {
        "category": category.id,
        "title": "Test Listing",
        "description": "Test Description",
        "price": 100,
        "currency": "UZS",
        "lat": 0,
        "lng": 0,
        "address_text": "Test Address"
    }
    response = api_client.post(reverse('listing-list'), data)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_verified_user_can_create_listing(api_client, verified_user, category):
    api_client.force_authenticate(user=verified_user)
    data = {
        "category": category.id,
        "title": "Test Listing",
        "description": "Test Description",
        "price": 100,
        "currency": "UZS",
        "lat": 0,
        "lng": 0,
        "address_text": "Test Address"
    }
    response = api_client.post(reverse('listing-list'), data)
    assert response.status_code == status.HTTP_201_CREATED
    listing = Listing.objects.get(id=response.data['id'])
    assert listing.status == 'pending'

@pytest.mark.django_db
def test_pending_listing_not_visible_to_others(api_client, verified_user, other_user, category):
    listing = Listing.objects.create(
        user=verified_user, category=category, title="Pending Listing", 
        description="Desc", price=100, lat=0, lng=0, address_text="Addr", status='pending',
        expires_at=timezone.now() + timedelta(days=30)
    )
    api_client.force_authenticate(user=other_user)
    response = api_client.get(reverse('listing-detail', kwargs={'pk': listing.id}))
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_pending_listing_visible_to_owner(api_client, verified_user, category):
    listing = Listing.objects.create(
        user=verified_user, category=category, title="Pending Listing", 
        description="Desc", price=100, lat=0, lng=0, address_text="Addr", status='pending',
        expires_at=timezone.now() + timedelta(days=30)
    )
    api_client.force_authenticate(user=verified_user)
    response = api_client.get(reverse('listing-detail', kwargs={'pk': listing.id}))
    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == str(listing.id)

@pytest.mark.django_db
def test_expires_at_auto_calculated(api_client, verified_user, category):
    api_client.force_authenticate(user=verified_user)
    data = {
        "category": category.id,
        "title": "Test Listing",
        "description": "Test Description",
        "price": 100,
        "currency": "UZS",
        "lat": 0,
        "lng": 0,
        "address_text": "Test Address",
    }
    response = api_client.post(reverse('listing-list'), data)
    listing = Listing.objects.get(id=response.data['id'])
    assert listing.expires_at is not None
    delta = listing.expires_at - timezone.now()
    assert timedelta(days=29) < delta <= timedelta(days=30)

@pytest.mark.django_db
def test_favorite_toggle_flow(api_client, auth_client, user, category):
    listing = Listing.objects.create(
        user=user, category=category, title="Test", description="Desc", 
        price=100, lat=0, lng=0, address_text="Addr", status='active',
        expires_at=timezone.now() + timedelta(days=30)
    )
    url = reverse('listing-favorite', kwargs={'pk': listing.id})
    
    # Add
    response = auth_client.post(url)
    assert response.status_code == status.HTTP_201_CREATED
    assert Favorite.objects.filter(user=user, listing=listing).exists()
    
    # Remove
    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Favorite.objects.filter(user=user, listing=listing).exists()

@pytest.mark.django_db
def test_owner_can_update_listing(api_client, auth_client, user, category):
    listing = Listing.objects.create(
        user=user, category=category, title="Test", description="Desc", 
        price=100, lat=0, lng=0, address_text="Addr", status='active',
        expires_at=timezone.now() + timedelta(days=30)
    )
    url = reverse('listing-detail', kwargs={'pk': listing.id})
    data = {"title": "New Title", "category": category.id, "price": 200, "description": "Desc", "lat": 0, "lng": 0, "address_text": "Addr"}
    
    response = auth_client.put(url, data)
    assert response.status_code == status.HTTP_200_OK
    listing.refresh_from_db()
    assert listing.title == "New Title"

@pytest.mark.django_db
def test_other_user_cannot_update_listing(api_client, other_user, user, category):
    listing = Listing.objects.create(
        user=user, category=category, title="Test", description="Desc", 
        price=100, lat=0, lng=0, address_text="Addr", status='active',
        expires_at=timezone.now() + timedelta(days=30)
    )
    api_client.force_authenticate(user=other_user)
    url = reverse('listing-detail', kwargs={'pk': listing.id})
    data = {"title": "New Title", "category": category.id, "price": 200, "description": "Desc", "lat": 0, "lng": 0, "address_text": "Addr"}
    
    response = api_client.put(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_listing_photo_limit_enforced(api_client, verified_user, category):
    plan = Plan.objects.create(
        name="Free", slug="free", price=0, billing_period_days=30,
        max_active_listings=10, max_monthly_new_listings=10,
        max_photos_per_listing=2, max_videos_per_listing=1,
        listing_duration_days=30, reboost_interval_days=3, auto_listing_type="normal"
    )
    Subscription.objects.create(user=verified_user, plan=plan)
    api_client.force_authenticate(user=verified_user)

    data = {
        "category": category.id, "title": "Test", "description": "D", "price": 100,
        "lat": 0, "lng": 0, "address_text": "A",
        "uploaded_files": [_fake_image("a.jpg"), _fake_image("b.jpg"), _fake_image("c.jpg")],
    }
    response = api_client.post(reverse('listing-list'), data, format="multipart")

    assert response.status_code == 400

@pytest.mark.django_db
def test_listing_video_limit_enforced(api_client, verified_user, category):
    plan = Plan.objects.create(
        name="Free", slug="free", price=0, billing_period_days=30,
        max_active_listings=10, max_monthly_new_listings=10,
        max_photos_per_listing=6, max_videos_per_listing=1,
        listing_duration_days=30, reboost_interval_days=3, auto_listing_type="normal"
    )
    Subscription.objects.create(user=verified_user, plan=plan)
    api_client.force_authenticate(user=verified_user)

    data = {
        "category": category.id, "title": "Test", "description": "D", "price": 100,
        "lat": 0, "lng": 0, "address_text": "A",
        "uploaded_files": [_fake_video("a.mp4"), _fake_video("b.mp4")],
    }
    response = api_client.post(reverse('listing-list'), data, format="multipart")

    assert response.status_code == 400

@pytest.mark.django_db
@patch("apps.serializers.listing.get_video_duration_seconds", return_value=10.0)
def test_listing_within_media_limits_succeeds(mock_duration, api_client, verified_user, category):
    plan = Plan.objects.create(
        name="Free", slug="free", price=0, billing_period_days=30,
        max_active_listings=10, max_monthly_new_listings=10,
        max_photos_per_listing=2, max_videos_per_listing=1,
        listing_duration_days=30, reboost_interval_days=3, auto_listing_type="normal"
    )
    Subscription.objects.create(user=verified_user, plan=plan)
    api_client.force_authenticate(user=verified_user)

    data = {
        "category": category.id, "title": "Test", "description": "D", "price": 100,
        "lat": 0, "lng": 0, "address_text": "A",
        "uploaded_files": [_fake_image("a.jpg"), _fake_video("v.mp4")],
    }
    response = api_client.post(reverse('listing-list'), data, format="multipart")

    assert response.status_code == 201

@pytest.mark.django_db
def test_pro_plan_listing_gets_vip_type(api_client, verified_user, category):
    plan = Plan.objects.create(
        name="Pro", slug="pro", price=49000, billing_period_days=30,
        max_active_listings=15, max_monthly_new_listings=30,
        max_photos_per_listing=8, max_videos_per_listing=2,
        listing_duration_days=45, reboost_interval_days=1,
        auto_listing_type="vip",
    )
    Subscription.objects.create(user=verified_user, plan=plan)
    api_client.force_authenticate(user=verified_user)

    response = api_client.post(reverse('listing-list'), {
        "category": category.id, "title": "Test", "description": "D", "price": 100,
        "lat": 0, "lng": 0, "address_text": "A",
    })

    assert response.status_code == 201
    listing = Listing.objects.get(id=response.data['id'])
    assert listing.listing_type == "vip"

@pytest.mark.django_db
def test_free_plan_listing_stays_normal(api_client, verified_user, category):
    plan = Plan.objects.create(
        name="Free", slug="free", price=0, billing_period_days=30,
        max_active_listings=3, max_monthly_new_listings=2,
        max_photos_per_listing=6, max_videos_per_listing=1,
        listing_duration_days=30, reboost_interval_days=3,
        auto_listing_type="normal",
    )
    Subscription.objects.create(user=verified_user, plan=plan)
    api_client.force_authenticate(user=verified_user)

    response = api_client.post(reverse('listing-list'), {
        "category": category.id, "title": "Test", "description": "D", "price": 100,
        "lat": 0, "lng": 0, "address_text": "A",
    })

    assert response.status_code == 201
    listing = Listing.objects.get(id=response.data['id'])
    assert listing.listing_type == "normal"

@pytest.mark.django_db
def test_list_orders_top_then_vip_then_normal(api_client, verified_user, category):
    common = {
        "user": verified_user, "category": category, "description": "D", "price": 100,
        "lat": 0, "lng": 0, "address_text": "A", "status": "active",
        "expires_at": timezone.now() + timedelta(days=30),
    }
    Listing.objects.create(title="Oddiy", listing_type="normal", **common)
    Listing.objects.create(title="Vip", listing_type="vip", **common)
    Listing.objects.create(title="Top", listing_type="top", **common)

    response = api_client.get(reverse('listing-list'))

    assert response.status_code == 200
    titles = [item["title"] for item in response.data]
    assert titles == ["Top", "Vip", "Oddiy"]

@pytest.mark.django_db
def test_list_ordering_by_price_respects_type_priority(api_client, verified_user, category):
    common = {
        "user": verified_user, "category": category, "description": "D",
        "lat": 0, "lng": 0, "address_text": "A", "status": "active",
        "expires_at": timezone.now() + timedelta(days=30),
    }
    Listing.objects.create(title="Top qimmat", listing_type="top", price=5000, **common)
    Listing.objects.create(title="Oddiy arzon", listing_type="normal", price=100, **common)

    response = api_client.get(reverse('listing-list'), {"ordering": "price"})

    assert response.status_code == 200
    titles = [item["title"] for item in response.data]
    assert titles == ["Top qimmat", "Oddiy arzon"]


@pytest.mark.django_db
def test_expire_listings_command(category, verified_user):
    from django.core.management import call_command

    expired_listing = Listing.objects.create(
        user=verified_user, category=category, title="Eski", description="D",
        price=100, lat=0, lng=0, address_text="A", status="active",
        expires_at=timezone.now() - timedelta(days=1),
    )
    still_active_listing = Listing.objects.create(
        user=verified_user, category=category, title="Yangi", description="D",
        price=100, lat=0, lng=0, address_text="A", status="active",
        expires_at=timezone.now() + timedelta(days=10),
    )
    pending_expired = Listing.objects.create(
        user=verified_user, category=category, title="Kutilmoqda", description="D",
        price=100, lat=0, lng=0, address_text="A", status="pending",
        expires_at=timezone.now() - timedelta(hours=1),
    )

    call_command("expire_listings")

    expired_listing.refresh_from_db()
    still_active_listing.refresh_from_db()
    pending_expired.refresh_from_db()

    assert expired_listing.status == "expired"
    assert still_active_listing.status == "active"
    assert pending_expired.status == "expired"
