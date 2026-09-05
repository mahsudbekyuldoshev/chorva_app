from datetime import timedelta

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
def test_listing_photo_limit_enforced(auth_client, verified_user, category):
    plan = Plan.objects.create(
        name="Free", slug="free", price=0, billing_period_days=30,
        max_active_listings=10, max_monthly_new_listings=10,
        max_photos_per_listing=2, max_videos_per_listing=1,
        listing_duration_days=30, reboost_interval_days=3,
    )
    Subscription.objects.create(user=verified_user, plan=plan)
    auth_client.force_authenticate(user=verified_user)

    data = {
        "category": category.id, "title": "Test", "description": "D", "price": 100,
        "lat": 0, "lng": 0, "address_text": "A",
        "uploaded_files": [_fake_image("a.jpg"), _fake_image("b.jpg"), _fake_image("c.jpg")],
    }
    response = auth_client.post(reverse('listing-list'), data, format="multipart")

    assert response.status_code == 400

@pytest.mark.django_db
def test_listing_video_limit_enforced(auth_client, verified_user, category):
    plan = Plan.objects.create(
        name="Free", slug="free", price=0, billing_period_days=30,
        max_active_listings=10, max_monthly_new_listings=10,
        max_photos_per_listing=6, max_videos_per_listing=1,
        listing_duration_days=30, reboost_interval_days=3,
    )
    Subscription.objects.create(user=verified_user, plan=plan)
    auth_client.force_authenticate(user=verified_user)

    data = {
        "category": category.id, "title": "Test", "description": "D", "price": 100,
        "lat": 0, "lng": 0, "address_text": "A",
        "uploaded_files": [_fake_video("a.mp4"), _fake_video("b.mp4")],
    }
    response = auth_client.post(reverse('listing-list'), data, format="multipart")

    assert response.status_code == 400

@pytest.mark.django_db
def test_listing_within_media_limits_succeeds(auth_client, verified_user, category):
    plan = Plan.objects.create(
        name="Free", slug="free", price=0, billing_period_days=30,
        max_active_listings=10, max_monthly_new_listings=10,
        max_photos_per_listing=2, max_videos_per_listing=1,
        listing_duration_days=30, reboost_interval_days=3,
    )
    Subscription.objects.create(user=verified_user, plan=plan)
    auth_client.force_authenticate(user=verified_user)

    data = {
        "category": category.id, "title": "Test", "description": "D", "price": 100,
        "lat": 0, "lng": 0, "address_text": "A",
        "uploaded_files": [_fake_image("a.jpg"), _fake_video("v.mp4")],
    }
    response = auth_client.post(reverse('listing-list'), data, format="multipart")

    assert response.status_code == 201
