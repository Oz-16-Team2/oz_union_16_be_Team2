import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.models import Comment, CommentLike, Post
from apps.users.models import User

# 모든 테스트에서 DB 접근이 필요하므로 마킹
pytestmark = pytest.mark.django_db


class TestPostCommentListCreate:
    """
    REQ-COMM-001 댓글 작성
    REQ-COMM-002 댓글 목록 조회
    """

    # --- POST (댓글 작성) ---

    def test_create_comment_success(self, api_client: APIClient, test_user: User, test_post: Post) -> None:
        """댓글 작성 성공 : 201"""
        api_client.force_authenticate(user=test_user)
        url = f"/api/v1/posts/{test_post.id}/comments"
        data = {"content": "테스트 댓글 내용"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["content"] == "테스트 댓글 내용"
        assert response.data["nickname"] == test_user.nickname
        assert Comment.objects.filter(post_id=test_post.id).count() == 1

    def test_create_comment_unauthorized(self, api_client: APIClient, test_post: Post) -> None:
        """[예외] 비로그인 유저가 작성을 시도할 경우 : 401 Unauthorized"""
        url = f"/api/v1/posts/{test_post.id}/comments"
        data = {"content": "로그인 안하고 쓰기"}

        response = api_client.post(url, data, format="json")

        # 인증 정보가 아예 없는 경우(Anonymous) 401을 반환하는 듯?
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "error_detail" in response.data

    def test_create_comment_validation_error(self, api_client: APIClient, test_user: User, test_post: Post) -> None:
        """[예외] 댓글 글자 수 500자 초과 : 400"""
        api_client.force_authenticate(user=test_user)
        url = f"/api/v1/posts/{test_post.id}/comments"
        data = {"content": "A" * 502}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error_detail" in response.data
        assert "content" in response.data["error_detail"]

    def test_create_comment_post_not_found(self, api_client: APIClient, test_user: User) -> None:
        """[예외] 존재하지 않는 게시글에 댓글 작성 시도 : 404"""
        api_client.force_authenticate(user=test_user)
        url = "/api/v1/posts/99999/comments"
        data = {"content": "없는 글에 댓글 쓰기"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error_detail" in response.data

    # --- GET (댓글 목록 조회) ---

    def test_get_comment_success_unauthenticated(self, api_client: APIClient, test_user: User, test_post: Post) -> None:
        """비로그인 유저의 댓글 목록 조회 성공 200"""
        comment = Comment.objects.create(user_id=test_user.id, post_id=test_post.id, content="테스트 댓글")
        CommentLike.objects.create(user_id=test_user.id, comment_id=comment.id)

        url = f"/api/v1/posts/{test_post.id}/comments"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"] if isinstance(response.data, dict) else response.data

        assert len(results) == 1
        assert results[0]["content"] == "테스트 댓글"
        assert results[0]["like_count"] == 1
        assert results[0]["is_liked"] is False

    def test_get_comments_success_authenticated_liked(
        self, api_client: APIClient, test_user: User, test_post: Post
    ) -> None:
        """로그인 유저의 목록 조회 시 본인 좋아요(is_liked) 여부 확인"""
        comment = Comment.objects.create(user_id=test_user.id, post_id=test_post.id, content="내 댓글")
        CommentLike.objects.create(user_id=test_user.id, comment_id=comment.id)

        api_client.force_authenticate(user=test_user)
        url = f"/api/v1/posts/{test_post.id}/comments"

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"] if isinstance(response.data, dict) else response.data
        assert results[0]["like_count"] == 1
        assert results[0]["is_liked"] is True
