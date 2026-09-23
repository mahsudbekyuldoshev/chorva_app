import pytest
from django.urls import reverse

from apps.models import Banner


@pytest.mark.django_db
def test_banner_list_is_public(api_client):
    Banner.objects.create(link_type="none")

    response = api_client.get(reverse('banner-list'))

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["link_type"] == "none"

@pytest.mark.django_db
def test_banner_view_increments_count(api_client):
    banner = Banner.objects.create(link_type="none")

    response = api_client.post(reverse('banner-view', kwargs={'pk': banner.id}))

    assert response.status_code == 200
    assert response.data["view_count"] == 1
    banner.refresh_from_db()
    assert banner.view_count == 1

@pytest.mark.django_db
def test_banner_with_category_link(api_client, category):
    Banner.objects.create(link_type="category", category=category)

    response = api_client.get(reverse('banner-list'))

    assert response.status_code == 200
    assert response.data[0]["category_id"] == str(category.id)
