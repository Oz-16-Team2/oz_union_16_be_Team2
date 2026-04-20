from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.posts.models import PostLike


@pytest.mark.django_db
class TestPostLike:
    @pytest.fixture(autouse=True)
    def _setup(self, test_user: Any, test_post: Any) -> None:
        self.user = test_user
        self.post = test_post

    def test_post_like_success(self, api_client: APIClient) -> None:
        url = reverse("post-likes", kwargs={"post_id": self.post.id})

        api_client.force_authenticate(user=self.user)
        response: Response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_liked"] is True
        assert PostLike.objects.filter(post=self.post, user=self.user).exists()

    def test_post_like_toggle_off(self, api_client: APIClient) -> None:
        url = reverse("post-likes", kwargs={"post_id": self.post.id})

        PostLike.objects.create(post=self.post, user=self.user)

        api_client.force_authenticate(user=self.user)
        response: Response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_liked"] is False
        assert not PostLike.objects.filter(post=self.post, user=self.user).exists()

    def test_post_like_404_not_found(self, api_client: APIClient) -> None:
        invalid_url = reverse("post-likes", kwargs={"post_id": 99999})

        api_client.force_authenticate(user=self.user)
        response: Response = api_client.post(invalid_url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "postId" in response.data["error_detail"]

    def test_post_like_401_unauthorized(self, api_client: APIClient) -> None:
        url = reverse("post-likes", kwargs={"post_id": self.post.id})

        response: Response = api_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
