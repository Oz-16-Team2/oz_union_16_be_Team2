from unittest.mock import MagicMock, patch  # MagicMock 추가

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestPresignedUrlAPI:
    @patch("apps.posts.views.post_public_views.boto3.client")
    def test_get_presigned_url_success(self, mock_boto_client: MagicMock) -> None:
        user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword",
            nickname="testurl",
        )

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("presigned-url")

        mock_s3 = mock_boto_client.return_value
        fake_url = "https://jaksim-fake-url.com/test.png"
        mock_s3.generate_presigned_url.return_value = fake_url

        data = {"filename": "my_cat.png"}
        response = client.post(url, data, format="json")

        assert response.status_code == 200
        assert response.data["detail"]["presigned_url"] == fake_url
        assert mock_s3.generate_presigned_url.called is True
