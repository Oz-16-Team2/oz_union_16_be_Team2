import uuid
<<<<<<< HEAD
from typing import Any, cast
=======
>>>>>>> 13d0857 (chore: 테스트 코드 디버깅)

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.models import Comment, Post
from apps.users.models import User


<<<<<<< HEAD
# ==========================================
# 1. 댓글 목록 조회 및 작성 (REQ-COMM-001, 002)
# ==========================================
@pytest.mark.django_db
class TestPostCommentListCreateView:
=======
@pytest.mark.django_db
class TestPostCommentListCreate:
>>>>>>> 13d0857 (chore: 테스트 코드 디버깅)
    """
    REQ-COMM-001 댓글 작성
    REQ-COMM-002 댓글 목록 조회
    """

    @pytest.fixture
    def api_client(self) -> APIClient:
<<<<<<< HEAD
=======
        """API 호출을 위한 클라이언트 객체"""
>>>>>>> 13d0857 (chore: 테스트 코드 디버깅)
        return APIClient()

    @pytest.fixture
    def user(self) -> User:
<<<<<<< HEAD
        # 💡 [Best Practice] uuid를 활용하여 매번 완벽하게 유니크한 독립적인 유저를 생성합니다.
        unique_id = uuid.uuid4().hex[:8]
        return User.objects.create(email=f"test_{unique_id}@test.com", nickname=f"user_{unique_id}")

    @pytest.fixture
    def post(self, user: User) -> Post:
        post = Post()
        post.user_id = user.id
        post.save()
        return post

    # POST
    def test_create_comment_success(self, api_client: APIClient, user: User, post: Post) -> None:
        api_client.force_authenticate(user=user)
        url = f"/api/v1/posts/{post.id}/comments"
        data = {"content": "쉬마려워요"}
=======
        """uuid를 활용하여 DB 오염을 방지하는 유니크 유저 생성"""
        uid = uuid.uuid4().hex[:8]
        return User.objects.create_user(email=f"user_{uid}@test.com", nickname=f"nick_{uid}", password="password123")

    @pytest.fixture
    def post(self, user: User) -> Post:
        """테스트용 게시글 생성"""
        return Post.objects.create(user_id=user.id)

    def test_create_comment_success(self, api_client: APIClient, user: User, post: Post) -> None:
        """[기능] 댓글 작성 성공 (201)"""
        api_client.force_authenticate(user=user)
        url = f"/api/v1/posts/{post.id}/comments"
        data = {"content": "테스트 댓글입니다."}
>>>>>>> 13d0857 (chore: 테스트 코드 디버깅)

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
<<<<<<< HEAD
        assert response.data["content"] == "쉬마려워요"
        assert response.data["nickname"] == user.nickname
        assert Comment.objects.filter(post_id=post.id).count() == 1

    def test_create_comment_unauthorized(self, api_client: APIClient, post: Post) -> None:
        url = f"/api/v1/posts/{post.id}/comments"
        data = {"content": "로그인 안하고 쓰기"}

        response = api_client.post(url, data, format="json")

        assert "error_detail" in response.data

    def test_create_comment_validation_error(self, api_client: APIClient, user: User, post: Post) -> None:
        api_client.force_authenticate(user=user)
        url = f"/api/v1/posts/{post.id}/comments"
        data = {"content": "A" * 502}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error_detail" in response.data
        assert "content" in response.data["error_detail"]

    def test_create_comment_post_not_found(self, api_client: APIClient, user: User) -> None:
        api_client.force_authenticate(user=user)
        url = "/api/v1/posts/99999/comments"
        data = {"content": " 없는 글에 댓글 쓰기"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error_detail" in response.data

    # GET
    def test_get_comment_success_unauthenticated(self, api_client: APIClient, user: User, post: Post) -> None:
        comment = Comment.objects.create(user_id=user.id, post_id=post.id, content="테스트 댓글")
        CommentLike.objects.create(user_id=user.id, comment_id=comment.id)

        url = f"/api/v1/posts/{post.id}/comments"

=======
        assert response.data["content"] == "테스트 댓글입니다."
        assert Comment.objects.filter(post_id=post.id).count() == 1

    def test_create_comment_unauthorized(self, api_client: APIClient, post: Post) -> None:
        """[예외] 비로그인 유저 접근 차단 (401)"""
        url = f"/api/v1/posts/{post.id}/comments"
        data = {"content": "로그인 안 함"}

        response = api_client.post(url, data, format="json")

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        assert "error_detail" in response.data

    def test_get_comment_success_unauthenticated(self, api_client: APIClient, user: User, post: Post) -> None:
        """[기능] 비로그인 유저 목록 조회 성공 (200)"""
        Comment.objects.create(user_id=user.id, post_id=post.id, content="댓글")

        url = f"/api/v1/posts/{post.id}/comments"
>>>>>>> 13d0857 (chore: 테스트 코드 디버깅)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

<<<<<<< HEAD
        assert len(results) == 1
        assert results[0]["content"] == "테스트 댓글"
        assert results[0]["like_count"] == 1
        assert results[0]["is_liked"] is False

    def test_get_comments_success_authenticated_liked(self, api_client: APIClient, user: User, post: Post) -> None:
        comment = Comment.objects.create(user_id=user.id, post_id=post.id, content="내 댓글")
        CommentLike.objects.create(user_id=user.id, comment_id=comment.id)

        api_client.force_authenticate(user=user)
        url = f"/api/v1/posts/{post.id}/comments"

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"] if isinstance(response.data, dict) else response.data
        assert results[0]["like_count"] == 1
        assert results[0]["is_liked"] is True


# ==========================================
# 2. 댓글 수정 및 삭제 (REQ-COMM-003, 004)
# ==========================================
@pytest.mark.django_db
class TestPostCommentDetailView:
    """
    REQ-COMM-003 댓글 수정
    REQ-COMM-004 댓글 삭제
    """

    @pytest.fixture
    def api_client(self) -> APIClient:
        return APIClient()

    @pytest.fixture
    def setup_data(self) -> dict[str, Any]:
        # 💡 [Best Practice] uuid를 활용하여 권한 테스트용 유저들도 매번 독립적으로 생성합니다.
        author_id = uuid.uuid4().hex[:8]
        other_id = uuid.uuid4().hex[:8]

        user_author = User.objects.create(email=f"author_{author_id}@test.com", nickname=f"author_{author_id}")
        user_other = User.objects.create(email=f"other_{other_id}@test.com", nickname=f"other_{other_id}")

        post = Post()
        post.user_id = user_author.id
        post.save()

        # 테스트 타겟: 작성자가 쓴 댓글
        comment = Comment.objects.create(user_id=user_author.id, post_id=post.id, content="기존 댓글 내용입니다.")

        return {"user_author": user_author, "user_other": user_other, "post": post, "comment": comment}

    @pytest.fixture
    def user_author(self, setup_data: dict[str, Any]) -> User:
        return cast(User, setup_data["user_author"])

    @pytest.fixture
    def user_other(self, setup_data: dict[str, Any]) -> User:
        return cast(User, setup_data["user_other"])

    @pytest.fixture
    def post(self, setup_data: dict[str, Any]) -> Post:
        return cast(Post, setup_data["post"])

    @pytest.fixture
    def comment(self, setup_data: dict[str, Any]) -> Comment:
        return cast(Comment, setup_data["comment"])

    # PATCH (수정) 테스트
    def test_update_comment_success(
        self, api_client: APIClient, user_author: User, post: Post, comment: Comment
    ) -> None:
        """[기능] 본인 댓글 정상 수정 (200)"""
        api_client.force_authenticate(user=user_author)
        url = f"/api/v1/posts/{post.id}/comments/{comment.id}"
        data = {"content": "수정된 댓글 내용입니다!"}

        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        # DB 갱신 후 검증
        comment.refresh_from_db()
        assert comment.content == "수정된 댓글 내용입니다!"

    def test_update_comment_forbidden(
        self, api_client: APIClient, user_other: User, post: Post, comment: Comment
    ) -> None:
        """[예외] 남의 댓글 수정 시도 (403)"""
        api_client.force_authenticate(user=user_other)
        url = f"/api/v1/posts/{post.id}/comments/{comment.id}"
        data = {"content": "내가 남의 댓글을 수정해볼게"}

        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # DELETE (삭제) 테스트
    def test_delete_comment_success(
        self, api_client: APIClient, user_author: User, post: Post, comment: Comment
    ) -> None:
        """[기능] 본인 댓글 정상 삭제 및 Soft Delete, 목록 미노출 검증 (204)"""
        api_client.force_authenticate(user=user_author)
        url = f"/api/v1/posts/{post.id}/comments/{comment.id}"

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 1. DB에서 Soft Delete 확인
        comment.refresh_from_db()
        assert comment.deleted_at is not None

        # 2. 목록 조회 시 더 이상 안 보이는지 이중 검증
        list_url = f"/api/v1/posts/{post.id}/comments"
        list_response = api_client.get(list_url)
        results = list_response.data["results"] if isinstance(list_response.data, dict) else list_response.data

        assert len(results) == 0

    def test_delete_comment_forbidden(
        self, api_client: APIClient, user_other: User, post: Post, comment: Comment
    ) -> None:
        """[예외] 남의 댓글 삭제 시도 (403)"""
        api_client.force_authenticate(user=user_other)
        url = f"/api/v1/posts/{post.id}/comments/{comment.id}"

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
=======
        # 페이징 여부에 따른 데이터 추출 대응
        results = (
            response.data["results"]
            if isinstance(response.data, dict) and "results" in response.data
            else response.data
        )
        assert len(results) >= 1
>>>>>>> 13d0857 (chore: 테스트 코드 디버깅)
