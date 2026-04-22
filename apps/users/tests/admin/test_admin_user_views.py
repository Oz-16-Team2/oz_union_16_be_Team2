# apps/users/tests/admin/test_admin_user_views.py

from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.choices import ReportReasonType, TargetType, UserStatus
from apps.posts.models import Comment, Post
from apps.reports.models import Report
from apps.users.models import User


@pytest.fixture
def admin_user(db: object) -> User:
    return User.objects.create_user(
        email="admin-user@example.com",
        password="password123",
        nickname="admin_user",
        is_staff=True,
    )


@pytest.fixture
def normal_user(db: object) -> User:
    return User.objects.create_user(
        email="normal-user@example.com",
        password="password123",
        nickname="normal_user",
    )


@pytest.fixture
def other_user(db: object) -> User:
    return User.objects.create_user(
        email="other-user@example.com",
        password="password123",
        nickname="other_user",
        total_goals_count=12,
    )


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user_activity_data(normal_user: User, other_user: User) -> None:
    post1 = Post.objects.create(
        user=normal_user,
        title="유저1 게시글 1",
        content="내용1",
    )
    post2 = Post.objects.create(
        user=normal_user,
        title="유저1 게시글 2",
        content="내용2",
    )
    comment1 = Comment.objects.create(
        user=normal_user,
        post=post1,
        content="유저1 댓글 1",
    )
    comment2 = Comment.objects.create(
        user=normal_user,
        post=post2,
        content="유저1 댓글 2",
    )

    Report.objects.create(
        user=other_user,
        target_id=post1.id,
        target_type=TargetType.POST,
        reason_type=ReportReasonType.SPAM,
        reason_detail="게시글 신고 1",
    )
    Report.objects.create(
        user=other_user,
        target_id=post2.id,
        target_type=TargetType.POST,
        reason_type=ReportReasonType.ABUSE,
        reason_detail="게시글 신고 2",
    )
    Report.objects.create(
        user=other_user,
        target_id=comment1.id,
        target_type=TargetType.COMMENT,
        reason_type=ReportReasonType.SPAM,
        reason_detail="댓글 신고 1",
    )
    Report.objects.create(
        user=other_user,
        target_id=comment2.id,
        target_type=TargetType.COMMENT,
        reason_type=ReportReasonType.ABUSE,
        reason_detail="댓글 신고 2",
    )
    Report.objects.create(
        user=other_user,
        target_id=comment2.id,
        target_type=TargetType.COMMENT,
        reason_type=ReportReasonType.OTHER,
        reason_detail="댓글 신고 3",
    )


@pytest.mark.django_db
class TestAdminUserListAPIView:
    def test_admin_user_list_success(
        self,
        api_client: APIClient,
        admin_user: User,
        normal_user: User,
        other_user: User,
        user_activity_data: None,
    ) -> None:
        api_client.force_authenticate(user=admin_user)

        response = api_client.get(
            "/api/v1/admin/accounts",
            {
                "page": "1",
                "size": "10",
            },
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()["detail"]
        target = next(item for item in data if item["id"] == normal_user.id)

        assert target["email"] == normal_user.email
        assert target["nickname"] == normal_user.nickname
        assert target["status"] == "ACTIVE"
        assert target["total_goals_count"] == 0
        assert target["post_count"] == 2
        assert target["comment_count"] == 2
        assert target["post_report_count"] == 2
        assert target["comment_report_count"] == 3
        assert target["status_expires_at"] is None
        assert target["memo"] is None

    def test_admin_user_list_bad_request(
        self,
        api_client: APIClient,
        admin_user: User,
    ) -> None:
        api_client.force_authenticate(user=admin_user)

        response = api_client.get(
            "/api/v1/admin/accounts",
            {
                "page": "0",
                "size": "10",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"error_detail": "잘못된 요청입니다."}

    def test_admin_user_list_unauthorized(
        self,
        api_client: APIClient,
    ) -> None:
        response = api_client.get(
            "/api/v1/admin/accounts",
            {
                "page": "1",
                "size": "10",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {"error_detail": "관리자 인증이 필요합니다."}

    def test_admin_user_list_forbidden(
        self,
        api_client: APIClient,
        normal_user: User,
    ) -> None:
        api_client.force_authenticate(user=normal_user)

        response = api_client.get(
            "/api/v1/admin/accounts",
            {
                "page": "1",
                "size": "10",
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"error_detail": "권한이 없습니다."}


@pytest.mark.django_db
class TestAdminUserStatusUpdateAPIView:
    def test_admin_user_status_update_success(
        self,
        api_client: APIClient,
        admin_user: User,
        normal_user: User,
    ) -> None:
        api_client.force_authenticate(user=admin_user)

        response = api_client.patch(
            f"/api/v1/admin/accounts/{normal_user.id}",
            {
                "status": "SUSPENDED",
                "status_expires_at": "2026-05-01T00:00:00Z",
                "memo": "도배성 게시글 작성",
            },
            format="json",
        )

        normal_user.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"detail": "사용자 계정 상태가 수정되었습니다."}
        assert normal_user.status == UserStatus.SUSPENDED
        assert normal_user.memo == "도배성 게시글 작성"
        assert normal_user.status_expires_at is not None

    def test_admin_user_status_update_bad_request(
        self,
        api_client: APIClient,
        admin_user: User,
        normal_user: User,
    ) -> None:
        api_client.force_authenticate(user=admin_user)

        response = api_client.patch(
            f"/api/v1/admin/accounts/{normal_user.id}",
            {
                "status": "WRONG_STATUS",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"error_detail": "잘못된 요청입니다."}

    def test_admin_user_status_update_not_found(
        self,
        api_client: APIClient,
        admin_user: User,
    ) -> None:
        api_client.force_authenticate(user=admin_user)

        response = api_client.patch(
            "/api/v1/admin/accounts/999999",
            {
                "status": "RESTRICTED",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"error_detail": "사용자를 찾을 수 없습니다."}

    def test_admin_user_status_update_unauthorized(
        self,
        api_client: APIClient,
        normal_user: User,
    ) -> None:
        response = api_client.patch(
            f"/api/v1/admin/accounts/{normal_user.id}",
            {
                "status": "RESTRICTED",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {"error_detail": "관리자 인증이 필요합니다."}

    def test_admin_user_status_update_forbidden(
        self,
        api_client: APIClient,
        normal_user: User,
        other_user: User,
    ) -> None:
        api_client.force_authenticate(user=normal_user)

        response = api_client.patch(
            f"/api/v1/admin/accounts/{other_user.id}",
            {
                "status": "RESTRICTED",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"error_detail": "권한이 없습니다."}

def test_admin_user_list_filter_by_status(
    self,
    api_client: APIClient,
    admin_user: User,
    normal_user: User,
) -> None:
    normal_user.status = UserStatus.SUSPENDED
    normal_user.save(update_fields=["status", "updated_at"])

    api_client.force_authenticate(user=admin_user)

    response = api_client.get(
        "/api/v1/admin/accounts",
        {
            "status": "SUSPENDED",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["detail"]
    assert len(data) >= 1
    assert all(item["status"] == "SUSPENDED" for item in data)

def test_admin_user_status_update_active_clears_expire_and_memo(
    self,
    api_client: APIClient,
    admin_user: User,
    normal_user: User,
) -> None:
    normal_user.status = UserStatus.SUSPENDED
    normal_user.memo = "기존 메모"
    normal_user.status_expires_at = "2026-05-01T00:00:00Z"  # 실제론 datetime 넣기
    normal_user.save()

    api_client.force_authenticate(user=admin_user)

    response = api_client.patch(
        f"/api/v1/admin/accounts/{normal_user.id}",
        {
            "status": "ACTIVE",
            "status_expires_at": None,
            "memo": None,
        },
        format="json",
    )

    normal_user.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert normal_user.status == UserStatus.ACTIVE
    assert normal_user.status_expires_at is None
    assert normal_user.memo is None