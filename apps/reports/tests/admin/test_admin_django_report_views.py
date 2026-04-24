from __future__ import annotations

import uuid

import pytest
from django.test import Client

from apps.core.choices import CommentStatus, PostStatus, ReportActionType, ReportReasonType, ReportStatus, TargetType
from apps.posts.models import Comment, Post
from apps.reports.models import Report, ReportAction
from apps.users.models import User


@pytest.fixture
def admin_client(db: object) -> Client:
    admin_user = User.objects.create_superuser(
        email=f"admin_report_{uuid.uuid4().hex}@test.com",
        password="1234",
    )
    client = Client()
    client.force_login(admin_user)
    return client


@pytest.fixture
def user(db: object) -> User:
    return User.objects.create_user(
        email=f"user_report_{uuid.uuid4().hex}@test.com",
        password="1234",
        nickname=f"user_{uuid.uuid4().hex[:8]}",
    )


@pytest.fixture
def post_report(user: User) -> Report:
    post = Post.objects.create(
        user=user,
        title="신고 테스트 게시글",
        content="신고 테스트 게시글 내용",
    )
    return Report.objects.create(
        user=user,
        target_id=post.id,
        target_type=TargetType.POST,
        reason_type=ReportReasonType.ABUSE,
        reason_detail="게시글 신고 테스트",
    )


@pytest.fixture
def comment_report(user: User) -> Report:
    post = Post.objects.create(
        user=user,
        title="댓글 신고 테스트 게시글",
        content="댓글 신고 테스트 게시글 내용",
    )
    comment = Comment.objects.create(
        post=post,
        user=user,
        content="신고 테스트 댓글",
    )
    return Report.objects.create(
        user=user,
        target_id=comment.id,
        target_type=TargetType.COMMENT,
        reason_type=ReportReasonType.SPAM,
        reason_detail="댓글 신고 테스트",
    )


@pytest.mark.django_db
class TestDjangoAdminReportViews:
    def test_report_list(self, admin_client: Client, post_report: Report) -> None:
        response = admin_client.get("/admin/reports/report/")

        assert response.status_code == 200
        assert "delete_selected" not in str(response.content)

    def test_report_target_preview_has_post_link(self, admin_client: Client, post_report: Report) -> None:
        response = admin_client.get("/admin/reports/report/")

        assert response.status_code == 200
        assert f"/admin/posts/post/{post_report.target_id}/change/" in response.content.decode()

    def test_delete_post_report_action(self, admin_client: Client, post_report: Report) -> None:
        response = admin_client.post(
            "/admin/reports/report/",
            {
                "action": "delete_target_and_handle",
                "_selected_action": [str(post_report.id)],
                "memo": "정책 위반으로 삭제",
            },
            follow=True,
        )

        post_report.refresh_from_db()
        post = Post.objects.get(id=post_report.target_id)
        report_action = ReportAction.objects.get(report=post_report)

        assert response.status_code == 200
        assert post_report.status == ReportStatus.HANDLED
        assert post.status == PostStatus.DELETED
        assert post.deleted_at is not None
        assert report_action.action_type == ReportActionType.DELETE
        assert report_action.memo == "정책 위반으로 삭제"

    def test_keep_comment_report_action(self, admin_client: Client, comment_report: Report) -> None:
        response = admin_client.post(
            "/admin/reports/report/",
            {
                "action": "keep_target_and_dismiss",
                "_selected_action": [str(comment_report.id)],
                "memo": "문제 없음으로 유지",
            },
            follow=True,
        )

        comment_report.refresh_from_db()
        comment = Comment.objects.get(id=comment_report.target_id)
        report_action = ReportAction.objects.get(report=comment_report)

        assert response.status_code == 200
        assert comment_report.status == ReportStatus.DISMISSED
        assert comment.status == CommentStatus.ACTIVE
        assert comment.deleted_at is None
        assert report_action.action_type == ReportActionType.KEEP
        assert report_action.memo == "문제 없음으로 유지"

    def test_already_handled_report_is_not_processed_again(self, admin_client: Client, post_report: Report) -> None:
        admin_client.post(
            "/admin/reports/report/",
            {
                "action": "keep_target_and_dismiss",
                "_selected_action": [str(post_report.id)],
                "memo": "1차 처리",
            },
            follow=True,
        )

        response = admin_client.post(
            "/admin/reports/report/",
            {
                "action": "delete_target_and_handle",
                "_selected_action": [str(post_report.id)],
                "memo": "중복 처리",
            },
            follow=True,
        )

        post_report.refresh_from_db()

        assert response.status_code == 200
        assert post_report.status == ReportStatus.DISMISSED
        assert ReportAction.objects.filter(report=post_report).count() == 1