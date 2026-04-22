import uuid

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.models import Post
from apps.users.models import User


@pytest.mark.django_db
class TestMyPosts:
    @pytest.fixture
    def api_client(self) -> APIClient:
        return APIClient()

    @pytest.fixture
    def user(self) -> User:
        unique_id = uuid.uuid4().hex[:8]
        return User.objects.create(email=f"me_test_{unique_id}@test.com", nickname=f"user_{unique_id}")

    @pytest.fixture
    def other_user(self) -> User:
        unique_id = uuid.uuid4().hex[:8]
        return User.objects.create(email=f"other_test_{unique_id}@test.com", nickname=f"other_{unique_id}")

    def test_my_posts_unauthenticated(self, api_client: APIClient) -> None:

        url = "/api/v1/posts/me"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_my_posts_success(self, api_client: APIClient, user: User) -> None:

        Post.objects.create(user=user, title="내 글 1", content="내용 1")
        Post.objects.create(user=user, title="내 글 2", content="내용 2")

        api_client.force_authenticate(user=user)
        url = "/api/v1/posts/me"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        body = response.data
        assert body["total_count"] == 2
        assert len(body["posts"]) == 2
        assert body["posts"][0]["nickname"] == user.nickname

    def test_my_posts_isolation(self, api_client: APIClient, user: User, other_user: User) -> None:

        Post.objects.create(user=user, title="내 글", content="내용")
        Post.objects.create(user=other_user, title="남의 글", content="내용")

        api_client.force_authenticate(user=user)
        url = "/api/v1/posts/me"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_count"] == 1
        assert response.data["posts"][0]["title"] == "내 글"

    def test_my_posts_pagination(self, api_client: APIClient, user: User) -> None:

        for i in range(5):
            Post.objects.create(user=user, title=f"글 {i}", content="내용")

        api_client.force_authenticate(user=user)

        url = "/api/v1/posts/me?page=0&size=2"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["posts"]) == 2
        assert response.data["total_count"] == 5

        url = "/api/v1/posts/me?page=2&size=2"
        response = api_client.get(url)
        assert len(response.data["posts"]) == 1
