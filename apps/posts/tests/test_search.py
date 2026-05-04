import uuid

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.models import Post
from apps.users.models import User


@pytest.mark.django_db
class TestPostSearch:
    @pytest.fixture
    def api_client(self) -> APIClient:
        return APIClient()

    @pytest.fixture
    def user(self) -> User:
        unique_id = uuid.uuid4().hex[:8]
        return User.objects.create(email=f"search_test_{unique_id}@test.com", nickname=f"user_{unique_id}")

    def test_search_success(self, api_client: APIClient, user: User) -> None:
        p1 = Post(user_id=user.id, title="오늘도 운동 완료", content="운동 열심히 했습니다.")
        p1.save()

        p2 = Post(user_id=user.id, title="다른 글", content="내용 없음")
        p2.save()

        url = "/api/v1/posts/search?keyword=운동"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        body = response.data["detail"]
        assert body["keyword"] == "운동"
        assert body["total_count"] == 1
        first = body["search_results"][0]
        assert first["post_id"] == p1.id
        assert first["title"] == "오늘도 운동 완료"
        assert first["nickname"] == user.nickname

    def test_search_bad_keyword(self, api_client: APIClient) -> None:
        url = "/api/v1/posts/search?keyword=ㅇ"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "keyword" in response.data["error_detail"]

    def test_search_no_match(self, api_client: APIClient, user: User) -> None:
        Post.objects.create(user_id=user.id, title="운동 아님", content="다른 내용")
        url = "/api/v1/posts/search?keyword=없는키워드"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        body = response.data["detail"]
        assert body["total_count"] == 0
        assert len(body["search_results"]) == 0
