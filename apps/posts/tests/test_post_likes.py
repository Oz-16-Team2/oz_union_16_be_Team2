import uuid

import pytest
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
        url = f"/api/v1/posts/{post.id}/likes"

        response = api_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED
        assert PostLike.objects.filter(user_id=user.id, post_id=post.id).exists()

    def test_post_like_duplicate(self, api_client: APIClient, user: User, post: Post) -> None:

        PostLike.objects.create(user_id=user.id, post_id=post.id)
        api_client.force_authenticate(user=user)
        url = f"/api/v1/posts/{post.id}/likes"

        response = api_client.post(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not PostLike.objects.filter(user_id=user.id, post_id=post.id).exists()

    def test_post_unlike_success(self, api_client: APIClient, user: User, post: Post) -> None:
        PostLike.objects.create(user_id=user.id, post_id=post.id)
        api_client.force_authenticate(user=user)
        url = f"/api/v1/posts/{post.id}/likes"

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not PostLike.objects.filter(user_id=user.id, post_id=post.id).exists()

    def test_post_unlike_not_found(self, api_client: APIClient, user: User, post: Post) -> None:
        api_client.force_authenticate(user=user)
        url = f"/api/v1/posts/{post.id}/likes"

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        err = response.data.get("error_detail")
        assert err is not None
        assert "좋아요 기록을 찾을 수 없습니다." in str(err)
