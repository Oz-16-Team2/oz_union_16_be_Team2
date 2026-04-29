from datetime import timedelta
from typing import TYPE_CHECKING

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.posts.models import Post
from apps.votes.models import Vote

User = get_user_model()

if TYPE_CHECKING:
    from apps.users.models import User as UserType
else:
    UserType = User


BASE_URL = "/api/v1/posts/"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db: None) -> UserType:
    return User.objects.create_user(
        email="test@test.com",
        password="1234",
        nickname="tester",
    )


@pytest.fixture
def post(db: None, user: UserType) -> Post:
    return Post.objects.create(
        user=user,
        title="테스트",
        content="내용",
        is_private=False,
    )


@pytest.mark.django_db
class TestPosts:
    def test_post_list(self, client: APIClient) -> None:
        res: Response = client.get(BASE_URL)

        assert res.status_code == 200

        body = res.data
        assert "posts" in body
        assert "page" in body
        assert "size" in body
        assert "total_count" in body

    def test_post_list_my_fail(self, client: APIClient) -> None:
        res: Response = client.get(f"{BASE_URL}?scope=MY")

        assert res.status_code == 401
        assert "error_detail" in res.data
        assert "Authorization" in res.data["error_detail"]

    def test_post_create(self, client: APIClient, user: UserType) -> None:
        client.force_authenticate(user)

        res: Response = client.post(
            BASE_URL,
            {"title": "생성", "content": "내용", "has_goal": False, "has_vote": False},
            format="json",
        )

        assert res.status_code == 201

        body = res.data
        assert body["detail"] == "게시글 작성이 완료되었습니다."
        assert "post_id" in body

    def test_post_create_with_vote_uses_string_options(self, client: APIClient, user: UserType) -> None:
        client.force_authenticate(user)
        start_at = timezone.now()
        end_at = start_at + timedelta(days=3)

        res: Response = client.post(
            BASE_URL,
            {
                "title": "투표 생성",
                "content": "내용",
                "has_goal": False,
                "has_vote": True,
                "vote": {
                    "options": ["예", "아니오"],
                    "start_at": start_at.date().isoformat(),
                    "end_at": end_at.date().isoformat(),
                },
            },
            format="json",
        )


        assert res.status_code == 201

        vote = Vote.objects.get(post_id=res.data["post_id"])
        assert list(vote.options.order_by("sort_order").values_list("content", flat=True)) == ["예", "아니오"]

    def test_post_detail(self, client: APIClient, post: Post) -> None:
        res: Response = client.get(f"{BASE_URL}{post.id}/")

        assert res.status_code == 200

        body = res.data
        assert body["post_id"] == post.id
        assert "content" in body

    def test_post_patch(self, client: APIClient, user: UserType, post: Post) -> None:
        client.force_authenticate(user)

        res: Response = client.patch(
            f"{BASE_URL}{post.id}/",
            {"title": "수정"},
            format="json",
        )

        assert res.status_code == 200
        assert res.data["detail"] == "게시글 수정이 완료되었습니다."

    def test_post_delete(self, client: APIClient, user: UserType, post: Post) -> None:
        client.force_authenticate(user)

        res: Response = client.delete(f"{BASE_URL}{post.id}/")

        assert res.status_code == 200
        assert res.data["detail"] == "게시글 삭제가 완료되었습니다."
