import pytest
from django.urls import reverse

from apps.models import Favorite, Listing


@pytest.mark.django_db
@pytest.mark.django_db
def test_favourites_list_returns_id_array(auth_client, verified_user, category):
    from datetime import timedelta

    from django.utils import timezone
    listing = Listing.objects.create(
        user=verified_user, category=category, title="T", description="D",
        price=100, lat=0, lng=0, address_text="A", status="active",
        expires_at=timezone.now() + timedelta(days=30),
    )
    Favorite.objects.create(user=verified_user, listing=listing)
    auth_client.force_authenticate(user=verified_user)

    response = auth_client.get(reverse('favourite-list-mobile'))

    assert response.status_code == 200
    assert response.data == [str(listing.id)]

@pytest.mark.django_db
def test_favourites_toggle(auth_client, verified_user, category):
    from datetime import timedelta

    from django.utils import timezone
    listing = Listing.objects.create(
        user=verified_user, category=category, title="T", description="D",
        price=100, lat=0, lng=0, address_text="A", status="active",
        expires_at=timezone.now() + timedelta(days=30),
    )
    auth_client.force_authenticate(user=verified_user)
    url = reverse('favourite-toggle', kwargs={'product_id': listing.id})

    add_response = auth_client.post(url)
    remove_response = auth_client.delete(url)

    assert add_response.status_code == 204
    assert remove_response.status_code == 204
    assert not Favorite.objects.filter(user=verified_user, listing=listing).exists()
