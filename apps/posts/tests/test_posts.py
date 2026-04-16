from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.posts.models import Post

User = get_user_model()

# 🔥 여기 중요 (슬래시 포함)
BASE_URL = "/api/v1/posts/"


@pytest.fixture
def setup_data() -> dict[str, Any]:
    client = APIClient()

    user = User.objects.create_user(
        email="test@test.com",
        password="1234",
        nickname="tester",
    )

    post = Post.objects.create(
        user=user,
        title="테스트",
        content="내용",
        is_private=False,
    )

    return {"client": client, "user": user, "post": post}


@pytest.mark.django_db
class TestPosts:
    def test_post_list(self, setup_data: dict[str, Any]) -> None:
        res = setup_data["client"].get(BASE_URL)

        assert res.status_code == 200

        body = res.data["detail"]
        assert "posts" in body
        assert "page" in body
        assert "size" in body
        assert "total_count" in body

    def test_post_list_my_fail(self, setup_data: dict[str, Any]) -> None:
        res = setup_data["client"].get(f"{BASE_URL}?scope=MY")

        assert res.status_code == 401
        assert "error_detail" in res.data
        assert "Authorization" in res.data["error_detail"]

    def test_post_create(self, setup_data: dict[str, Any]) -> None:
        client = setup_data["client"]
        client.force_authenticate(setup_data["user"])

        res = client.post(
            BASE_URL,
            {"title": "생성", "content": "내용", "has_goal": False, "has_vote": False},
            format="json",
        )

        assert res.status_code == 201

        body = res.data["detail"]
        assert body["detail"] == "게시글 작성이 완료되었습니다."
        assert "post_id" in body

    def test_post_detail(self, setup_data: dict[str, Any]) -> None:
        post = setup_data["post"]

        # 🔥 슬래시 포함
        res = setup_data["client"].get(f"{BASE_URL}{post.id}/")

        assert res.status_code == 200

        body = res.data["detail"]
        assert body["post_id"] == post.id
        assert "content" in body

    def test_post_patch(self, setup_data: dict[str, Any]) -> None:
        client = setup_data["client"]
        client.force_authenticate(setup_data["user"])
        post = setup_data["post"]

        res = client.patch(
            f"{BASE_URL}{post.id}/",
            {"title": "수정"},
            format="json",
        )

        assert res.status_code == 200
        assert res.data["detail"] == "게시글 수정이 완료되었습니다."

    def test_post_delete(self, setup_data: dict[str, Any]) -> None:
        client = setup_data["client"]
        client.force_authenticate(setup_data["user"])
        post = setup_data["post"]

        res = client.delete(f"{BASE_URL}{post.id}/")

        assert res.status_code == 200
        assert res.data["detail"] == "게시글 삭제가 완료되었습니다."
