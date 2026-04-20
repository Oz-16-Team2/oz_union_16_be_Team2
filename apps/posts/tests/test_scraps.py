import uuid

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.models import Post, Scrap
from apps.users.models import User


@pytest.mark.django_db
class TestScrapViews:
    """
    REQ-SCRP-001 (POST): 스크랩 생성
    REQ-SCRP-002 (GET): 내 스크랩 목록 조회
    REQ-SCRP-003 (DELETE): 스크랩 삭제
    """

    @pytest.fixture
    def api_client(self) -> APIClient:
        return APIClient()

    @pytest.fixture
    def user(self) -> User:
        """테스트를 수행할 주체 유저"""
        unique_id = uuid.uuid4().hex[:8]
        return User.objects.create(email=f"scrap_{unique_id}@test.com", nickname=f"user_{unique_id}")

    @pytest.fixture
    def post(self, user: User) -> Post:
        """테스트용 대상 게시글"""
        post = Post()
        post.user_id = user.id
        post.title = "테스트 게시글 제목"
        post.save()
        return post

    # ==========================================
    # 1. REQ-SCRP-001: 스크랩 생성 (POST) 테스트
    # ==========================================
    def test_create_scrap_success(self, api_client: APIClient, user: User, post: Post) -> None:
        """[기능] 정상적인 스크랩 생성 (201)"""
        api_client.force_authenticate(user=user)
        url = f"/api/v1/posts/{post.id}/scraps"

        response = api_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED
        # DB에 실제로 데이터가 적재되었는지 교차 검증 (Edge Case 방지)
        assert Scrap.objects.filter(user_id=user.id, post_id=post.id).exists()

    def test_create_scrap_duplicate_conflict(self, api_client: APIClient, user: User, post: Post) -> None:
        """[예외] 이미 스크랩한 게시글을 다시 스크랩 시도 (409 Conflict)"""
        Scrap.objects.create(user_id=user.id, post_id=post.id)

        api_client.force_authenticate(user=user)
        url = f"/api/v1/posts/{post.id}/scraps"
        response = api_client.post(url)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "error_detail" in response.data
        assert "이미 스크랩한 게시글입니다" in str(response.data["error_detail"])

    def test_create_scrap_post_not_found(self, api_client: APIClient, user: User) -> None:
        """[예외] 존재하지 않는 게시글 스크랩 시도 (404 Not Found)"""
        api_client.force_authenticate(user=user)
        url = "/api/v1/posts/999999/scraps"  # 불가능한 ID라 가정
        response = api_client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ==========================================
    # 2. REQ-SCRP-003: 스크랩 취소/삭제 (DELETE) 테스트
    # ==========================================
    def test_delete_scrap_success(self, api_client: APIClient, user: User, post: Post) -> None:
        """[기능] 정상적인 스크랩 취소 (204)"""
        Scrap.objects.create(user_id=user.id, post_id=post.id)

        api_client.force_authenticate(user=user)
        url = f"/api/v1/posts/{post.id}/scraps"
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Scrap.objects.filter(user_id=user.id, post_id=post.id).exists()  # DB에서 삭제되었는지 확인

    def test_delete_scrap_not_found(self, api_client: APIClient, user: User, post: Post) -> None:
        """[예외] 스크랩하지도 않은 게시글을 취소 시도 (404 Not Found)"""
        api_client.force_authenticate(user=user)
        url = f"/api/v1/posts/{post.id}/scraps"

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "스크랩 기록을 찾을 수 없습니다" in str(response.data["error_detail"])

    # ==========================================
    # 3. REQ-SCRP-002: 내 스크랩 목록 조회 (GET) 테스트
    # ==========================================
    def test_get_scrap_list_success_and_isolation(self, api_client: APIClient, user: User) -> None:
        """
        [기능/엣지케이스]
        내 스크랩 목록이 정확히 조회되는지,
        그리고 '남이 스크랩한 데이터'는 내 목록에 노출되지 않는지(데이터 격리) 확인합니다. (200 OK)
        """
        # 1. 내 스크랩용 게시글 2개 생성
        my_post1 = Post(user_id=user.id, title="내 첫번째 글")
        my_post1.save()
        my_post2 = Post(user_id=user.id, title="내 두번째 글")
        my_post2.save()

        Scrap.objects.create(user_id=user.id, post_id=my_post1.id)
        Scrap.objects.create(user_id=user.id, post_id=my_post2.id)

        # 2. 남의 스크랩 데이터 생성
        unique_id = uuid.uuid4().hex[:8]
        other_user = User.objects.create(email=f"other_{unique_id}@test.com", nickname=f"other_{unique_id}")

        other_post = Post(user_id=other_user.id, title="남의 글")
        other_post.save()
        Scrap.objects.create(user_id=other_user.id, post_id=other_post.id)

        # 3. API 호출
        api_client.force_authenticate(user=user)
        url = "/api/v1/posts/scraps"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        data = response.data
        assert data["total_count"] == 2  # 내 스크랩 2개만 카운트되어야 함 (남의 것 1개는 무시)
        assert len(data["results"]) == 2

    def test_get_scrap_list_unauthorized(self, api_client: APIClient) -> None:
        """[예외] 비로그인 유저가 스크랩 목록 조회 시도 (401 Unauthorized)"""
        url = "/api/v1/posts/scraps"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
