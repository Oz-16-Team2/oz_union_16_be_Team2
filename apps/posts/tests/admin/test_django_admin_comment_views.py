from __future__ import annotations

from typing import Any

import pytest
from django.test import Client

from apps.core.choices import PostStatus
from apps.posts.models import Comment, Post
from apps.users.models import User


@pytest.fixture
def admin_client(db: Any) -> Client:
    user = User.objects.create_superuser(
        email="admin_comment@test.com",
        password="1234",
    )
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def comments(db: Any) -> list[Comment]:
    user = User.objects.create_user(
        email="comment_user@test.com",
        password="1234",
        nickname="댓글작성자",
    )
    post = Post.objects.create(
        user=user,
        title="댓글 테스트 게시글",
        content="댓글 테스트 게시글 내용",
        status=PostStatus.ACTIVE,
    )

    return [
        Comment.objects.create(
            post=post,
            user=user,
            content=f"댓글 테스트 {index}",
        )
        for index in range(10)
    ]


@pytest.mark.django_db
class TestDjangoAdminCommentViews:
    def test_comment_list(self, admin_client: Client, comments: list[Comment]) -> None:
        response = admin_client.get("/admin/posts/comment/")
        assert response.status_code == 200

    def test_comment_search_all(self, admin_client: Client, comments: list[Comment]) -> None:
        response = admin_client.get("/admin/posts/comment/?q=1")
        assert response.status_code == 200

    def test_comment_search_by_comment_id(self, admin_client: Client, comments: list[Comment]) -> None:
        comment = comments[0]
        response = admin_client.get(f"/admin/posts/comment/?filter_type=comment_id&q={comment.id}")
        assert response.status_code == 200

    def test_comment_search_by_post_id(self, admin_client: Client, comments: list[Comment]) -> None:
        post_id = comments[0].post_id
        response = admin_client.get(f"/admin/posts/comment/?filter_type=post_id&q={post_id}")
        assert response.status_code == 200

    def test_comment_search_by_user_id(self, admin_client: Client, comments: list[Comment]) -> None:
        user_id = comments[0].user_id
        response = admin_client.get(f"/admin/posts/comment/?filter_type=user_id&q={user_id}")
        assert response.status_code == 200
