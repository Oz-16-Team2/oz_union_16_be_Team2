import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.constants import PROFILE_IMAGE_URL_MAP


@pytest.mark.django_db
class TestProfileImageListAPI:
    def test_get_profile_image_list_success(self) -> None:
        client = APIClient()

        url = reverse("profile-list")
        response = client.get(url)

        expected_data = [
            {
                "code": code,
                "image_url": image_url,
            }
            for code, image_url in PROFILE_IMAGE_URL_MAP.items()
        ]

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"detail": expected_data}
