from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.choices import CommentStatus
from apps.posts.models import Comment, Post
from apps.users.models import User


@pytest.fixture(scope="function")
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture(scope="function")
def admin_user(db: object) -> User:
    return User.objects.create_user(
        email="admin@example.com",
        password="password123",
        nickname="admin",
        is_staff=True,
    )


@pytest.fixture(scope="function")
def normal_user(db: object) -> User:
    return User.objects.create_user(
        email="user@example.com",
        password="password123",
        nickname="user1",
    )


@pytest.fixture(scope="function")
def post(normal_user: User) -> Post:
    return Post.objects.create(
        user=normal_user,
        title="테스트 게시글",
        content="테스트 내용",
    )


@pytest.fixture(scope="function")
def comment(normal_user: User, post: Post) -> Comment:
    return Comment.objects.create(
        post=post,
        user=normal_user,
        content="삭제 대상 댓글",
    )


@pytest.mark.django_db
def test_admin_comment_delete_success(
    api_client: APIClient,
    admin_user: User,
    comment: Comment,
) -> None:
    api_client.force_authenticate(user=admin_user)

    response = api_client.delete(f"/api/v1/admin/comments/{comment.id}")

    comment.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"detail": "댓글이 삭제되었습니다."}
    assert comment.status == CommentStatus.DELETED
    assert comment.deleted_at is not None


@pytest.mark.django_db
def test_admin_comment_delete_unauthorized(
    api_client: APIClient,
    comment: Comment,
) -> None:
    response = api_client.delete(f"/api/v1/admin/comments/{comment.id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"error_detail": "관리자 인증이 필요합니다."}


@pytest.mark.django_db
def test_admin_comment_delete_forbidden(
    api_client: APIClient,
    normal_user: User,
    comment: Comment,
) -> None:
    api_client.force_authenticate(user=normal_user)

    response = api_client.delete(f"/api/v1/admin/comments/{comment.id}")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"error_detail": "권한이 없습니다."}


@pytest.mark.django_db
def test_admin_comment_delete_not_found(
    api_client: APIClient,
    admin_user: User,
) -> None:
    api_client.force_authenticate(user=admin_user)

    response = api_client.delete("/api/v1/admin/comments/999999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"error_detail": "댓글을 찾을 수 없습니다."}