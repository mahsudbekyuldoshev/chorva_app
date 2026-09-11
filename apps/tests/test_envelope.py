import json
import uuid

import pytest
from django.urls import reverse

from apps.models import Category


@pytest.mark.django_db
def test_success_response_is_wrapped(api_client):
    Category.objects.create(name_uz="Qoramol", name_ru="КРС", name_en="Cattle")

    response = api_client.get(reverse('category-list'))
    body = json.loads(response.content)

    assert response.status_code == 200
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert body["data"][0]["name_uz"] == "Qoramol"


@pytest.mark.django_db
def test_validation_error_is_wrapped(auth_client):
    response = auth_client.post(reverse('report-create'), {"reason": "spam", "comment": "test"})
    body = json.loads(response.content)

    assert response.status_code == 400
    assert body["success"] is False
    assert "code" in body["error"]
    assert "message" in body["error"]


@pytest.mark.django_db
def test_not_found_error_is_wrapped(api_client):
    response = api_client.get(reverse('user-detail', kwargs={'id': uuid.uuid4()}))
    body = json.loads(response.content)

    assert response.status_code == 404
    assert body["success"] is False
    assert body["error"]["code"] == "NOT_FOUND"


@pytest.mark.django_db
def test_unauthenticated_error_is_wrapped(api_client):
    response = api_client.get(reverse('me'))
    body = json.loads(response.content)

    assert response.status_code in (401, 403)
    assert body["success"] is False
    assert "code" in body["error"]
