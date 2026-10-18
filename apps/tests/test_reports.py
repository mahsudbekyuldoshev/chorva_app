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


@pytest.mark.django_db
def test_user_report_endpoint_succeeds(auth_client, user, other_user):
    url = reverse('user-report')
    data = {
        "phone": other_user.phone,
        "reason_codes": ["spam", "fraud"],
        "message": "Inappropriate behavior",
    }
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    report = Report.objects.get(reporter=user, target_user=other_user)
    assert report.reason_codes == ["spam", "fraud"]
    assert report.comment == "Inappropriate behavior"


@pytest.mark.django_db
def test_user_report_invalid_phone(auth_client):
    url = reverse('user-report')
    data = {
        "phone": "998999999999",
        "reason_codes": ["spam"],
    }
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_report_self_fails(auth_client, user):
    url = reverse('user-report')
    data = {
        "phone": user.phone,
        "reason_codes": ["spam"],
    }
    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_report_deduplication(auth_client, user, other_user):
    url = reverse('user-report')
    data = {
        "phone": other_user.phone,
        "reason_codes": ["spam"],
    }
    response1 = auth_client.post(url, data)
    assert response1.status_code == status.HTTP_201_CREATED

    response2 = auth_client.post(url, data)
    assert response2.status_code == status.HTTP_200_OK
    assert Report.objects.filter(reporter=user, target_user=other_user).count() == 1

