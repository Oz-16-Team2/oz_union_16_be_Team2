from rest_framework import status
from rest_framework.test import APITestCase

from apps.posts.models import Comment, CommentLike, Post
from apps.users.models import User


class TestPostCommentListCreateView(APITestCase):
    """
    REQ-COMM-001 댓글 작성
    REQ-COMM-002 댓글 목록 조회
    """
    # setUpTestData에서 동적으로 할당될 변수들의 타입을 정적으로 미리 선언
    user: User
    post: Post

    @classmethod
    def setUpTestData(cls) -> None:

        # 공통으로 사용할 유저 생성
        cls.user = User.objects.create(email="test@test.com", nickname="testuser")
        # 공통으로 사용할 게시글 생성
        cls.post = Post()
        cls.post.user_id = cls.user.id
        cls.post.save()

    # POST

    def test_create_comment_success(self) -> None:
        """
        댓글 작성 성공 : 201
        """
        self.client.force_authenticate(user=self.user)
        url = f"/api/v1/posts/{self.post.id}/comments"
        data = {"content": "쉬마려워요"}

        response = self.client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["content"] == "쉬마려워요"
        assert response.data["nickname"] == self.user.nickname
        assert Comment.objects.filter(post_id=self.post.id).count() == 1

    def test_create_comment_unauthorized(self) -> None:
        """
        [예외] 비로그인 유저가 작성을 시도할 경우 : 401
        """
        url = f"/api/v1/posts/{self.post.id}/comments"
        data = {"content": "로그인 안하고 쓰기"}

        response = self.client.post(url, data, format="json")

        assert "error_detail" in response.data

    def test_create_comment_validation_error(self) -> None:
        """
        [예외] 댓글 글자 수 500자 초과 : 400
        """
        self.client.force_authenticate(user=self.user)
        url = f"/api/v1/posts/{self.post.id}/comments"
        data = {"content": "A" * 502}

        response = self.client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error_detail" in response.data
        assert "content" in response.data["error_detail"]

    def test_create_comment_post_not_found(self) -> None:
        """
        [예외] 존재하지 않는 게시글에 댓글 작성 시도 : 404
        """
        self.client.force_authenticate(user=self.user)
        url = "/api/v1/posts/99999/comments"
        data = {"content": " 없는 글에 댓글 쓰기"}

        response = self.client.post(url, data, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error_detail" in response.data

    # GET

    def test_get_comment_success_unauthenticated(self) -> None:
        """
        비로그인 유저의 댓글 목록 조회 성공 200
        좋아요 수 확인
        """
        # _id로 끝나는 파라미터에는 무조건 객체.id 형태로 숫자를 넘겨줘야 함, type:ignore 안써도 됨
        comment = Comment.objects.create(user_id=self.user.id, post_id=self.post.id, content="테스트 댓글")
        CommentLike.objects.create(user_id=self.user.id, comment_id=comment.id)

        url = f"/api/v1/posts/{self.post.id}/comments"

        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"] if isinstance(response.data, dict) else response.data

        assert len(results) == 1
        assert results[0]["content"] == "테스트 댓글"
        assert results[0]["like_count"] == 1  # 누군가 누른 1개가 카운트 되어야 함
        assert results[0]["is_liked"] is False  # 비로그인이므로 False

    def test_get_comments_success_authenticated_liked(self) -> None:
        """
        로그인 유저의 목록 조회 시 본인 좋아요(is_liked) 여부 확인
        """
        comment = Comment.objects.create(user_id=self.user.id, post_id=self.post.id, content="내 댓글")
        CommentLike.objects.create(user_id=self.user.id, comment_id=comment.id)

        self.client.force_authenticate(user=self.user)  # 로그인 처리
        url = f"/api/v1/posts/{self.post.id}/comments"

        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"] if isinstance(response.data, dict) else response.data
        assert results[0]["like_count"] == 1
        assert results[0]["is_liked"] is True  # 로그인한 내가 눌렀으므로 True!
