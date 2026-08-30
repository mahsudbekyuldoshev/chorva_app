import pytest
from django.urls import reverse
from rest_framework import status

from apps.models import Report


@pytest.mark.django_db
def test_report_requires_target(api_client, auth_client):
    data = {"reason": "spam", "comment": "test"}
    response = auth_client.post(reverse('report-create'), data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_report_with_target_user_succeeds(api_client, auth_client, other_user):
    data = {"reason": "spam", "comment": "test", "target_user": other_user.id}
    response = auth_client.post(reverse('report-create'), data)
    assert response.status_code == status.HTTP_201_CREATED
    assert Report.objects.filter(target_user=other_user).exists()
