import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.models import Comment, CommentLike, Post
from apps.users.models import User


@pytest.mark.django_db
class TestPostCommentListCreateView:
    """
    REQ-COMM-001 댓글 작성
    REQ-COMM-002 댓글 목록 조회
    """

    @pytest.fixture
    def api_client(self) -> APIClient:  # API 호출하는 클라이언트 객체
        return APIClient()

    @pytest.fixture
    def user(self) -> User:  # 테스트용 일반 유저
        return User.objects.create(email="test@test.com", nickname="testuser")

    @pytest.fixture
    def post(self, user: User) -> Post:  # 테스트용 대상 게시글
        post = Post()
        post.user_id = user.id
        post.save()
        return post

    # POST
    def test_create_comment_success(self, api_client: APIClient, user: User, post: Post) -> None:
        """
        댓글 작성 성공 케이스 201
        """
        api_client.force_authenticate(user=user)
        url = f"/api/v1/posts/{post.id}/comments"
        data = {"content": "쉬마려워요"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["content"] == "쉬마려워요"
        assert response.data["nickname"] == user.nickname
        assert Comment.objects.filter(post_id=post.id).count() == 1

    def test_create_comment_unauthorized(self, api_client: APIClient, post: Post) -> None:
        """
        [예외] 비로그인 유저가 작성을 시도할 경우 401
        """
        url = f"/api/v1/posts/{post.id}/comments"
        data = {"content": "로그인 안하고 쓰기"}

        response = api_client.post(url, data, format="json")

        assert "error_detail" in response.data

    def test_create_comment_validation_error(self, api_client: APIClient, user: User, post: Post) -> None:
        """
        [예외] 댓글 글자 수 500자 초과 400
        """
        api_client.force_authenticate(user=user)
        # [수정 4] URL 오타 수정: /post/ -> /posts/
        url = f"/api/v1/posts/{post.id}/comments"
        data = {"content": "A" * 502}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert "error_detail" in response.data
        assert "content" in response.data["error_detail"]

    def test_create_comment_post_not_found(self, api_client: APIClient, user: User) -> None:
        """
        [예외] 존재하지 않는 게시글에 댓글 작성 시도 404
        """
        api_client.force_authenticate(user=user)
        url = "/api/v1/posts/99999/comments"
        data = {"content": " 없는 글에 댓글 쓰기"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error_detail" in response.data

    # GET
    def test_get_comment_success_unauthenticated(self, api_client: APIClient, user: User, post: Post) -> None:
        """
        비로그인 유저의 댓글 목록 조회 성공 200
        좋아요 수 확인
        """
        # _id로 끝나는 파라미터에는 무조건 객체.id 형태로 숫자를 넘겨줘야 함, type:ignore 안써도 됨
        comment = Comment.objects.create(user_id=user.id, post_id=post.id, content="테스트 댓글")
        CommentLike.objects.create(user_id=user.id, comment_id=comment.id)

        url = f"/api/v1/posts/{post.id}/comments"

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"] if isinstance(response.data, dict) else response.data

        assert len(results) == 1
        assert results[0]["content"] == "테스트 댓글"
        assert results[0]["like_count"] == 1  # 누군가 누른 1개가 카운트 되어야 함
        assert results[0]["is_liked"] is False  # 비로그인이므로 False

    def test_get_comments_success_authenticated_liked(self, api_client: APIClient, user: User, post: Post) -> None:
        """
        로그인 유저의 목록 조회 시 본인 좋아요(is_liked) 여부 확인
        """
        comment = Comment.objects.create(user_id=user.id, post_id=post.id, content="내 댓글")
        CommentLike.objects.create(user_id=user.id, comment_id=comment.id)

        api_client.force_authenticate(user=user)  # 로그인 처리
        url = f"/api/v1/posts/{post.id}/comments"

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"] if isinstance(response.data, dict) else response.data
        assert results[0]["like_count"] == 1
        assert results[0]["is_liked"] is True  # 로그인한 내가 눌렀으므로 True!
