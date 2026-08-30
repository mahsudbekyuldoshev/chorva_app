from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.models import Favorite, Listing


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
