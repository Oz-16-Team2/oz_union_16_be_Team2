import uuid

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.models import Post, PostLike
from apps.users.models import User


@pytest.mark.django_db
class TestPostLikeOnly:
    @pytest.fixture
    def api_client(self) -> APIClient:
        return APIClient()

    @pytest.fixture
    def user(self) -> User:
        unique_id = uuid.uuid4().hex[:8]
        return User.objects.create(email=f"post_like_test_{unique_id}@test.com", nickname=f"user_{unique_id}")

    @pytest.fixture
    def post(self, user: User) -> Post:
        p = Post(user_id=user.id, title="제목", content="내용")
        p.save()
        return p

    def test_post_like_success(self, api_client: APIClient, user: User, post: Post) -> None:
        api_client.force_authenticate(user=user)
        url = reverse("post-like", kwargs={"post_id": post.id})

        response = api_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED
        assert PostLike.objects.filter(user_id=user.id, post_id=post.id).exists()

    def test_post_unlike_success(self, api_client: APIClient, user: User, post: Post) -> None:

        PostLike.objects.create(user_id=user.id, post_id=post.id)
        api_client.force_authenticate(user=user)
        url = reverse("post-like", kwargs={"post_id": post.id})

        response = api_client.post(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not PostLike.objects.filter(user_id=user.id, post_id=post.id).exists()

    def test_post_like_not_found(self, api_client: APIClient, user: User) -> None:
        api_client.force_authenticate(user=user)
        invalid_post_id = 99999
        url = reverse("post-like", kwargs={"post_id": invalid_post_id})

        response = api_client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error_detail" in response.data
        assert response.data["error_detail"]["postId"] == ["해당 게시글을 찾을 수 없습니다."]

    def test_post_like_unauthorized(self, api_client: APIClient, post: Post) -> None:

        url = reverse("post-like", kwargs={"post_id": post.id})

        response = api_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        assert "error_detail" in response.data
