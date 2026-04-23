import uuid

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.models import Comment, CommentLike, Post
from apps.users.models import User


@pytest.mark.django_db
class TestLikeViews:
    """
    REQ-POST-007 게시글 좋아요 및 취소
    REQ-COMM-004 댓글 좋아요 및 취소
    """

    # ==========================================
    # 1. Fixtures
    # ==========================================
    @pytest.fixture
    def api_client(self) -> APIClient:
        """API 호출을 위한 클라이언트 객체"""
        return APIClient()

    @pytest.fixture
    def user(self) -> User:
        unique_id = uuid.uuid4().hex[:8]
        return User.objects.create(email=f"like_test_{unique_id}@test.com", nickname=f"user_{unique_id}")

    @pytest.fixture
    def post(self, user: User) -> Post:
        """테스트용 대상 게시글을 생성."""
        post = Post()
        post.user_id = user.id
        post.save()
        return post

    @pytest.fixture
    def comment(self, user: User, post: Post) -> Comment:
        """테스트용 댓글을 생성합니다."""
        return Comment.objects.create(user_id=user.id, post_id=post.id, content="테스트용 댓글입니다.")

    # ==========================================
    # 3. REQ-COMM-004: 댓글 좋아요 테스트
    # ==========================================
    def test_comment_like_success(self, api_client: APIClient, user: User, comment: Comment) -> None:
        """[기능] 댓글 좋아요 성공 (201)"""
        api_client.force_authenticate(user=user)
        # URL 구조: /api/v1/posts/comments/{comment_id}/likes
        url = f"/api/v1/posts/comments/{comment.id}/likes"

        response = api_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED
        assert CommentLike.objects.filter(user_id=user.id, comment_id=comment.id).exists()

    def test_comment_like_soft_deleted(self, api_client: APIClient, user: User, comment: Comment) -> None:
        """[예외] Soft Delete 된 댓글에 좋아요 (404)"""
        from django.utils import timezone

        comment.deleted_at = timezone.now()
        comment.save()

        api_client.force_authenticate(user=user)
        url = f"/api/v1/posts/comments/{comment.id}/likes"

        response = api_client.post(url)

        # 삭제된 댓글은 찾을 수 없음. (404)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_comment_unlike_not_found(self, api_client: APIClient, user: User, comment: Comment) -> None:
        """[예외] 누르지 않은 좋아요를 취소(404)"""
        api_client.force_authenticate(user=user)
        url = f"/api/v1/posts/comments/{comment.id}/likes"

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "좋아요 기록을 찾을 수 없습니다." in response.data["error_detail"]
