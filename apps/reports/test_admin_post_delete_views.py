from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.models import Post
from apps.users.models import User


@pytest.fixture
def admin_user(db: object) -> User:
    return User.objects.create_user(
        email="admin-post@example.com",
        password="password123",
        nickname="admin_post",
        is_staff=True,
    )


@pytest.fixture
def normal_user(db: object) -> User:
    return User.objects.create_user(
        email="user-post@example.com",
        password="password123",
        nickname="user_post",
    )


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def post(normal_user: User) -> Post:
    return Post.objects.create(
        user=normal_user,
        title="관리자 게시글 삭제 테스트용",
        content="테스트 게시글 내용",
    )


@pytest.mark.django_db
class TestAdminPostDeleteAPIView:
    def test_admin_post_delete_success(
        self,
        api_client: APIClient,
        admin_user: User,
        post: Post,
    ) -> None:
        api_client.force_authenticate(user=admin_user)

        response = api_client.delete(f"/api/v1/admin/posts/{post.id}/delete")

        post.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"detail": "게시글이 삭제되었습니다."}
        assert str(post.status).lower() == "deleted"
        assert post.deleted_at is not None

    def test_admin_post_delete_unauthorized(
        self,
        api_client: APIClient,
        post: Post,
    ) -> None:
        response = api_client.delete(f"/api/v1/admin/posts/{post.id}/delete")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {"error_detail": "관리자 인증이 필요합니다."}

    def test_admin_post_delete_forbidden(
        self,
        api_client: APIClient,
        normal_user: User,
        post: Post,
    ) -> None:
        api_client.force_authenticate(user=normal_user)

        response = api_client.delete(f"/api/v1/admin/posts/{post.id}/delete")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"error_detail": "권한이 없습니다."}

    def test_admin_post_delete_not_found(
        self,
        api_client: APIClient,
        admin_user: User,
    ) -> None:
        api_client.force_authenticate(user=admin_user)

        response = api_client.delete("/api/v1/admin/posts/999999/delete")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"error_detail": "게시글을 찾을 수 없습니다."}

    def test_admin_post_delete_already_deleted_returns_not_found(
        self,
        api_client: APIClient,
        admin_user: User,
        post: Post,
    ) -> None:
        api_client.force_authenticate(user=admin_user)

        first_response = api_client.delete(f"/api/v1/admin/posts/{post.id}/delete")
        second_response = api_client.delete(f"/api/v1/admin/posts/{post.id}/delete")

        assert first_response.status_code == status.HTTP_200_OK
        assert second_response.status_code == status.HTTP_404_NOT_FOUND
        assert second_response.json() == {"error_detail": "게시글을 찾을 수 없습니다."}