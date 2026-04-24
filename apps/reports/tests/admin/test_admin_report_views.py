from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.choices import ReportReasonType, TargetType
from apps.posts.models import Comment, Post
from apps.reports.models import Report
from apps.users.models import User


@pytest.fixture
def admin_user(db: object) -> User:
    return User.objects.create_user(
        email="admin@example.com",
        password="password123",
        nickname="admin",
        is_staff=True,
    )


@pytest.fixture
def normal_user(db: object) -> User:
    return User.objects.create_user(
        email="user@example.com",
        password="password123",
        nickname="user",
    )


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def post(normal_user: User) -> Post:
    return Post.objects.create(
        user=normal_user,
        title="신고 테스트용 게시글",
        content="신고 테스트용 내용",
    )


@pytest.fixture
def comment(normal_user: User, post: Post) -> Comment:
    return Comment.objects.create(
        user=normal_user,
        post=post,
        content="신고 테스트용 댓글",
    )


@pytest.fixture
def report(comment: Comment, normal_user: User) -> Report:
    return Report.objects.create(
        user=normal_user,
        target_id=comment.id,
        target_type=TargetType.COMMENT,
        reason_type=ReportReasonType.SPAM,
        reason_detail="테스트 신고 사유",
    )


@pytest.fixture
def handled_report_comment(normal_user: User, post: Post) -> Comment:
    return Comment.objects.create(
        user=normal_user,
        post=post,
        content="DELETE 처리 테스트용 댓글",
    )


@pytest.fixture
def handled_report(handled_report_comment: Comment, normal_user: User) -> Report:
    return Report.objects.create(
        user=normal_user,
        target_id=handled_report_comment.id,
        target_type=TargetType.COMMENT,
        reason_type=ReportReasonType.SPAM,
        reason_detail="DELETE 처리 테스트용 신고",
    )


@pytest.fixture
def dismissed_report_comment(normal_user: User, post: Post) -> Comment:
    return Comment.objects.create(
        user=normal_user,
        post=post,
        content="KEEP 처리 테스트용 댓글",
    )


@pytest.fixture
def dismissed_report(dismissed_report_comment: Comment, normal_user: User) -> Report:
    return Report.objects.create(
        user=normal_user,
        target_id=dismissed_report_comment.id,
        target_type=TargetType.COMMENT,
        reason_type=ReportReasonType.SPAM,
        reason_detail="KEEP 처리 테스트용 신고",
    )


@pytest.mark.django_db
class TestAdminReportActionAPIView:
    def test_admin_report_action_delete_success(
        self,
        api_client: APIClient,
        admin_user: User,
        handled_report: Report,
        handled_report_comment: Comment,
    ) -> None:
        api_client.force_authenticate(user=admin_user)

        response = api_client.post(
            f"/api/v1/admin/reports/{handled_report.id}/actions",
            {
                "action_type": "DELETE",
                "memo": "정책 위반으로 삭제",
            },
            format="json",
        )

        handled_report.refresh_from_db()
        handled_report_comment.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"detail": "신고가 처리되었습니다."}
        assert str(handled_report.status).lower() == "handled"
        assert handled_report.admin_id == admin_user.id
        assert handled_report.handled_at is not None
        assert str(handled_report_comment.status).lower() == "deleted"
        assert handled_report_comment.deleted_at is not None

    def test_admin_report_action_keep_success(
        self,
        api_client: APIClient,
        admin_user: User,
        dismissed_report: Report,
        dismissed_report_comment: Comment,
    ) -> None:
        api_client.force_authenticate(user=admin_user)

        response = api_client.post(
            f"/api/v1/admin/reports/{dismissed_report.id}/actions",
            {
                "action_type": "KEEP",
                "memo": "문제 없음으로 판단",
            },
            format="json",
        )

        dismissed_report.refresh_from_db()
        dismissed_report_comment.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"detail": "신고가 처리되었습니다."}
        assert str(dismissed_report.status).lower() == "dismissed"
        assert dismissed_report.admin_id == admin_user.id
        assert dismissed_report.handled_at is not None
        assert str(dismissed_report_comment.status).lower() == "active"
        assert dismissed_report_comment.deleted_at is None

    def test_admin_report_action_already_processed_returns_conflict(
        self,
        api_client: APIClient,
        admin_user: User,
        handled_report: Report,
    ) -> None:
        api_client.force_authenticate(user=admin_user)

        first_response = api_client.post(
            f"/api/v1/admin/reports/{handled_report.id}/actions",
            {
                "action_type": "DELETE",
                "memo": "첫 처리",
            },
            format="json",
        )
        second_response = api_client.post(
            f"/api/v1/admin/reports/{handled_report.id}/actions",
            {
                "action_type": "KEEP",
                "memo": "두 번째 처리 시도",
            },
            format="json",
        )

        assert first_response.status_code == status.HTTP_200_OK
        assert second_response.status_code == status.HTTP_409_CONFLICT
        assert second_response.json() == {"error_detail": "이미 처리된 신고입니다."}

    def test_admin_report_action_not_found(
        self,
        api_client: APIClient,
        admin_user: User,
    ) -> None:
        api_client.force_authenticate(user=admin_user)

        response = api_client.post(
            "/api/v1/admin/reports/999999/actions",
            {
                "action_type": "DELETE",
                "memo": "없는 신고 처리",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"error_detail": "신고를 찾을 수 없습니다."}


@pytest.mark.django_db
class TestAdminReportListAPIView:
    def test_admin_report_list_includes_target_status_action_type_and_memo(
        self,
        api_client: APIClient,
        admin_user: User,
        handled_report: Report,
        dismissed_report: Report,
    ) -> None:
        api_client.force_authenticate(user=admin_user)

        api_client.post(
            f"/api/v1/admin/reports/{handled_report.id}/actions",
            {
                "action_type": "DELETE",
                "memo": "삭제 처리 테스트",
            },
            format="json",
        )
        api_client.post(
            f"/api/v1/admin/reports/{dismissed_report.id}/actions",
            {
                "action_type": "KEEP",
                "memo": "유지 처리 테스트",
            },
            format="json",
        )

        response = api_client.get(
            "/api/v1/admin/reports",
            {
                "page": "1",
                "size": "10",
            },
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()["detail"]
        report_map = {item["id"]: item for item in data}

        handled_item = report_map[handled_report.id]
        dismissed_item = report_map[dismissed_report.id]

        assert handled_item["status"] == "HANDLED"
        assert handled_item["action_type"] == "DELETE"
        assert handled_item["memo"] == "삭제 처리 테스트"
        assert handled_item["target_preview"]["status"] == "DELETED"

        assert dismissed_item["status"] == "DISMISSED"
        assert dismissed_item["action_type"] == "KEEP"
        assert dismissed_item["memo"] == "유지 처리 테스트"
        assert dismissed_item["target_preview"]["status"] == "ACTIVE"

    def test_admin_report_list_filter_by_status(
        self,
        api_client: APIClient,
        admin_user: User,
        handled_report: Report,
    ) -> None:
        api_client.force_authenticate(user=admin_user)

        api_client.post(
            f"/api/v1/admin/reports/{handled_report.id}/actions",
            {
                "action_type": "DELETE",
                "memo": "삭제 처리 테스트",
            },
            format="json",
        )

        response = api_client.get(
            "/api/v1/admin/reports",
            {
                "status": "HANDLED",
                "page": "1",
                "size": "10",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["detail"]

        assert len(data) >= 1
        assert all(item["status"] == "HANDLED" for item in data)

    def test_admin_report_list_filter_by_target_type(
        self,
        api_client: APIClient,
        admin_user: User,
        report: Report,
    ) -> None:
        api_client.force_authenticate(user=admin_user)

        response = api_client.get(
            "/api/v1/admin/reports",
            {
                "target_type": "COMMENT",
                "page": "1",
                "size": "10",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["detail"]

        assert len(data) >= 1
        assert all(item["target_type"] == "COMMENT" for item in data)
