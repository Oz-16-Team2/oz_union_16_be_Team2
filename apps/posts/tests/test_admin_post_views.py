from __future__ import annotations

from typing import Any

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.choices import PostStatus, ProfileImageCode
from apps.posts.models import Comment, Post, PostLike, PostTag, Scrap, Tag
from apps.users.models import User
from apps.votes.models import Vote, VoteOption


@pytest.fixture(scope="class")
def admin_post_data(django_db_blocker: Any) -> dict[str, Any]:
    with django_db_blocker.unblock():
        admin_user = User.objects.create_user(
            email="admin_post@test.com",
            password="test1234",
            nickname="admin_post_user",
            is_staff=True,
        )
        normal_user = User.objects.create_user(
            email="user_post@test.com",
            password="test1234",
            nickname="normal_post_user",
            profile_image=ProfileImageCode.AVATAR_02,
            is_staff=False,
        )
        author = User.objects.create_user(
            email="author_post@test.com",
            password="test1234",
            nickname="author_post_user",
            profile_image=ProfileImageCode.AVATAR_01,
        )

        tag1 = Tag.objects.create(name="운동_post", is_active=True)
        tag2 = Tag.objects.create(name="공부_post", is_active=True)

        post_with_vote = Post.objects.create(
            user=author,
            title="오늘 목표 성공",
            content="운동 완료했습니다.",
            images=[
                "https://example.com/posts/post_1_img_1.png",
                "https://example.com/posts/post_1_img_2.png",
            ],
            is_private=False,
            goal_title="매일 운동하기",
            goal_progress=70,
            status=PostStatus.REPORTED,
        )
        post_without_vote = Post.objects.create(
            user=author,
            title="공부 인증합니다",
            content="오늘은 알고리즘 3문제 풀었습니다.",
            images=["https://example.com/posts/post_2_img_1.png"],
            is_private=False,
            status=PostStatus.ACTIVE,
        )

        PostTag.objects.create(post=post_with_vote, tag=tag1)
        PostTag.objects.create(post=post_without_vote, tag=tag2)

        Comment.objects.create(
            post=post_with_vote,
            user=normal_user,
            content="응원합니다!",
        )

        PostLike.objects.create(post=post_with_vote, user=author)
        PostLike.objects.create(post=post_with_vote, user=normal_user)
        Scrap.objects.create(post=post_with_vote, user=normal_user)

        vote = Vote.objects.create(
            post=post_with_vote,
            question="내일도 운동할까요?",
            start_at="2026-04-13T09:00:00Z",
            end_at="2026-04-14T09:00:00Z",
        )
        VoteOption.objects.create(vote=vote, content="찬성", sort_order=1)
        VoteOption.objects.create(vote=vote, content="반대", sort_order=2)

        return {
            "admin_user": admin_user,
            "normal_user": normal_user,
            "author": author,
            "tag1": tag1,
            "tag2": tag2,
            "post_with_vote": post_with_vote,
            "post_without_vote": post_without_vote,
            "vote": vote,
        }


@pytest.fixture
def fresh_post_data() -> dict[str, Any]:
    admin_user = User.objects.create_user(
        email="admin_post_fresh@test.com",
        password="test1234",
        nickname="admin_post_fresh_user",
        is_staff=True,
    )
    author = User.objects.create_user(
        email="author_post_fresh@test.com",
        password="test1234",
        nickname="author_post_fresh_user",
    )
    post = Post.objects.create(
        user=author,
        title="수정 테스트용 게시글",
        content="수정 테스트용 내용",
        is_private=False,
        status=PostStatus.ACTIVE,
    )

    return {
        "admin_user": admin_user,
        "author": author,
        "post": post,
    }


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
class TestAdminPostAPIView:
    def test_admin_can_get_post_list(self, api_client: APIClient, admin_post_data: dict[str, Any]) -> None:
        api_client.force_authenticate(user=admin_post_data["admin_user"])

        response = api_client.get(
            "/api/v1/admin/posts",
            {"page": 1, "size": 10},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "detail" in response.data
        assert len(response.data["detail"]) == 2

    def test_post_list_can_filter_by_has_vote(self, api_client: APIClient, admin_post_data: dict[str, Any]) -> None:
        api_client.force_authenticate(user=admin_post_data["admin_user"])

        response = api_client.get(
            "/api/v1/admin/posts",
            {"page": 1, "size": 10, "has_vote": True},
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["detail"]) == 1
        assert response.data["detail"][0]["id"] == admin_post_data["post_with_vote"].id

    def test_post_list_can_filter_by_status(self, api_client: APIClient, admin_post_data: dict[str, Any]) -> None:
        api_client.force_authenticate(user=admin_post_data["admin_user"])

        response = api_client.get(
            "/api/v1/admin/posts",
            {"page": "1", "size": "10", "status": "REPORTED"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["detail"]) == 1
        assert response.data["detail"][0]["status"] == "REPORTED"

    def test_post_list_returns_400_when_query_is_invalid(
        self,
        api_client: APIClient,
        admin_post_data: dict[str, Any],
    ) -> None:
        api_client.force_authenticate(user=admin_post_data["admin_user"])

        response = api_client.get(
            "/api/v1/admin/posts",
            {"page": 0, "size": 10},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error_detail"] == "잘못된 요청입니다."

    def test_post_list_returns_401_when_unauthenticated(self, api_client: APIClient) -> None:
        response = api_client.get(
            "/api/v1/admin/posts",
            {"page": 1, "size": 10},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["error_detail"] == "관리자 인증이 필요합니다."

    def test_post_list_returns_403_when_not_admin(self, api_client: APIClient, admin_post_data: dict[str, Any]) -> None:
        api_client.force_authenticate(user=admin_post_data["normal_user"])

        response = api_client.get(
            "/api/v1/admin/posts",
            {"page": 1, "size": 10},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["error_detail"] == "권한이 없습니다."

    def test_admin_can_get_post_detail(self, api_client: APIClient, admin_post_data: dict[str, Any]) -> None:
        api_client.force_authenticate(user=admin_post_data["admin_user"])

        response = api_client.get(f"/api/v1/admin/posts/{admin_post_data['post_with_vote'].id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"]["id"] == admin_post_data["post_with_vote"].id
        assert response.data["detail"]["title"] == "오늘 목표 성공"
        assert len(response.data["detail"]["comments"]) == 1
        assert response.data["detail"]["vote"] is not None

    def test_post_detail_returns_404_when_post_not_found(
        self,
        api_client: APIClient,
        admin_post_data: dict[str, Any],
    ) -> None:
        api_client.force_authenticate(user=admin_post_data["admin_user"])

        response = api_client.get("/api/v1/admin/posts/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["error_detail"] == "게시글을 찾을 수 없습니다."

    def test_admin_can_delete_post(self, api_client: APIClient, fresh_post_data: dict[str, Any]) -> None:
        api_client.force_authenticate(user=fresh_post_data["admin_user"])

        response = api_client.delete(f"/api/v1/admin/posts/{fresh_post_data['post'].id}/delete")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "게시글이 삭제되었습니다."

        fresh_post_data["post"].refresh_from_db()
        assert fresh_post_data["post"].deleted_at is not None

    def test_delete_post_returns_404_when_post_not_found(
        self,
        api_client: APIClient,
        admin_post_data: dict[str, Any],
    ) -> None:
        api_client.force_authenticate(user=admin_post_data["admin_user"])

        response = api_client.delete("/api/v1/admin/posts/99999/delete")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["error_detail"] == "게시글을 찾을 수 없습니다."

    def test_admin_can_update_post_status(self, api_client: APIClient, fresh_post_data: dict[str, Any]) -> None:
        api_client.force_authenticate(user=fresh_post_data["admin_user"])

        response = api_client.patch(
            f"/api/v1/admin/posts/{fresh_post_data['post'].id}/status",
            {"status": "REPORTED"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "게시글 상태가 수정되었습니다."

        fresh_post_data["post"].refresh_from_db()
        assert fresh_post_data["post"].status == PostStatus.REPORTED

    def test_update_post_status_returns_400_when_status_is_invalid(
        self,
        api_client: APIClient,
        fresh_post_data: dict[str, Any],
    ) -> None:
        api_client.force_authenticate(user=fresh_post_data["admin_user"])

        response = api_client.patch(
            f"/api/v1/admin/posts/{fresh_post_data['post'].id}/status",
            {"status": "WRONG"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error_detail"] == "잘못된 요청입니다."

    def test_update_post_status_returns_404_when_post_not_found(
        self,
        api_client: APIClient,
        admin_post_data: dict[str, Any],
    ) -> None:
        api_client.force_authenticate(user=admin_post_data["admin_user"])

        response = api_client.patch(
            "/api/v1/admin/posts/99999/status",
            {"status": "REPORTED"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["error_detail"] == "게시글을 찾을 수 없습니다."
