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
