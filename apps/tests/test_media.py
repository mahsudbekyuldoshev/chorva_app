from unittest.mock import patch

import pytest
from django.urls import reverse


@pytest.mark.django_db
@patch("apps.utils.storage._get_s3_client")
def test_media_presign_returns_urls(mock_client_factory, auth_client, user):
    mock_client = mock_client_factory.return_value
    mock_client.generate_presigned_url.return_value = "https://fake-upload-url.example.com/signed"
    auth_client.force_authenticate(user=user)

    response = auth_client.post(reverse('media-presign'), {"kind": "image", "ext": "jpg"})

    assert response.status_code == 200
    assert response.data["upload_url"] == "https://fake-upload-url.example.com/signed"
    assert response.data["public_url"].endswith(".jpg")

@pytest.mark.django_db
def test_media_presign_rejects_invalid_extension(auth_client, user):
    auth_client.force_authenticate(user=user)

    response = auth_client.post(reverse('media-presign'), {"kind": "image", "ext": "exe"})

    assert response.status_code == 400

@pytest.mark.django_db
def test_media_presign_requires_auth(api_client):
    response = api_client.post(reverse('media-presign'), {"kind": "image", "ext": "jpg"})

    assert response.status_code in (401, 403)
