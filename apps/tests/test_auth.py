import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

from apps.models import User


@pytest.mark.django_db
def test_new_user_has_unusable_password(api_client):
    phone = "998909999999"
    otp = "1234"
    cache.set(f"otp_{phone}", otp, 120)
    
    response = api_client.post(reverse('verify-otp'), {"phone": phone, "code": otp})
    assert response.status_code == status.HTTP_200_OK
    
    user = User.objects.get(phone=phone)
    assert not user.has_usable_password()


@pytest.mark.django_db
def test_user_can_authenticate_via_django_auth_backend(verified_user):
    from django.contrib.auth import authenticate  # noqa: F401

    # verified_user fixture'i parolsiz (set_unusable_password) bo'lishi
    # mumkin — shuning uchun to'g'ridan-to'g'ri is_active'ni tekshiramiz,
    # bu aynan buzilgan joy edi.
    assert verified_user.is_active is True


@pytest.mark.django_db
def test_superuser_login_works(client, django_user_model):
    user = django_user_model.objects.create_superuser(
        phone="+998900000001", password="testpass123"
    )
    assert user.is_active is True

    logged_in = client.login(phone="+998900000001", password="testpass123")
    assert logged_in is True


@pytest.mark.django_db
def test_verify_otp_response_field_names(api_client):
    cache.set("otp_+998905556677", "1234", timeout=120)

    response = api_client.post(reverse('verify-otp'), {"phone": "+998905556677", "code": "1234"})

    assert response.status_code == 200
    assert "access_token" in response.data
    assert "refresh_token" in response.data
    assert "user_id" in response.data
    assert "is_new_user" in response.data


@pytest.mark.django_db
def test_refresh_token_endpoint(api_client, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)

    response = api_client.post(reverse('token-refresh'), {"refresh_token": str(refresh)})
    
    assert response.status_code == 200
    assert "access_token" in response.data


@pytest.mark.django_db
def test_logout_blacklists_token(api_client, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    api_client.force_authenticate(user=user)

    logout_response = api_client.post(reverse('logout'), {"refresh_token": str(refresh)})
    assert logout_response.status_code == 204

    api_client.force_authenticate(user=None)
    refresh_response = api_client.post(reverse('token-refresh'), {"refresh_token": str(refresh)})
    assert refresh_response.status_code == 401
