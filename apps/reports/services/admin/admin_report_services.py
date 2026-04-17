from __future__ import annotations

from typing import Any

from django.utils import timezone

from apps.core.choices import (
    CommentStatus,
    PostStatus,
    ReportActionType,
    ReportStatus,
    TargetType,
)
from apps.core.exceptions import ConflictException, ResourceNotFoundException
from apps.posts.models import Comment, Post
from apps.reports.models import Report, ReportAction


class AdminReportService:
    @staticmethod
    def get_reports(
        *,
        status_value: str | None,
        target_type_value: str | None,
        page: int,
        size: int,
    ) -> list[dict[str, Any]]:
        queryset = Report.objects.select_related("user", "admin").order_by("-created_at")

        if status_value is not None:
            queryset = queryset.filter(status=status_value.lower())

        if target_type_value is not None:
            queryset = queryset.filter(target_type=target_type_value.lower())

        offset = (page - 1) * size
        reports = list(queryset[offset : offset + size])

        post_ids = [report.target_id for report in reports if report.target_type == TargetType.POST]
        comment_ids = [report.target_id for report in reports if report.target_type == TargetType.COMMENT]

        post_map = {
            post.id: post
            for post in Post.objects.filter(id__in=post_ids).only("id", "title")
        }
        comment_map = {
            comment.id: comment
            for comment in Comment.objects.filter(id__in=comment_ids).only("id", "content")
        }

        result: list[dict[str, Any]] = []
        for report in reports:
            target_preview: dict[str, Any]

            if report.target_type == TargetType.POST:
                post = post_map.get(report.target_id)
                target_preview = {
                    "id": report.target_id,
                    "title": post.title if post else "삭제되었거나 존재하지 않는 게시글",
                }
            else:
                comment = comment_map.get(report.target_id)
                target_preview = {
                    "id": report.target_id,
                    "content": comment.content if comment else "삭제되었거나 존재하지 않는 댓글",
                }

            result.append(
                {
                    "id": report.id,
                    "user_id": report.user_id,
                    "admin_id": report.admin_id,
                    "target_id": report.target_id,
                    "target_type": str(report.target_type).upper(),
                    "target_preview": target_preview,
                    "reason_type": str(report.reason_type).upper(),
                    "reason_detail": report.reason_detail,
                    "status": str(report.status).upper(),
                    "handled_at": report.handled_at,
                    "created_at": report.created_at,
                    "updated_at": report.updated_at,
                }
            )

        return result

    @staticmethod
    def process_report(
        *,
        report_id: int,
        action_type: str,
        memo: str,
        admin_id: int,
    ) -> None:
        try:
            report = Report.objects.get(id=report_id)
        except Report.DoesNotExist as exc:
            raise ResourceNotFoundException("신고를 찾을 수 없습니다.") from exc

        if report.status != ReportStatus.PENDING:
            raise ConflictException("이미 처리된 신고입니다.")

        if action_type == ReportActionType.DELETE.upper():
            if report.target_type == TargetType.POST:
                AdminReportService._delete_post(report.target_id)
            elif report.target_type == TargetType.COMMENT:
                AdminReportService._delete_comment(report.target_id)

            report.status = ReportStatus.HANDLED

        elif action_type == ReportActionType.KEEP.upper():
            report.status = ReportStatus.DISMISSED

        else:
            raise ConflictException("잘못된 처리 타입입니다.")

        report.admin_id = admin_id
        report.handled_at = timezone.now()
        report.save(update_fields=["status", "admin_id", "handled_at", "updated_at"])

        ReportAction.objects.create(
            report=report,
            admin_id=admin_id,
            action_type=action_type.lower(),
            memo=memo,
        )

    @staticmethod
    def _delete_post(post_id: int) -> None:
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist as exc:
            raise ResourceNotFoundException("게시글을 찾을 수 없습니다.") from exc

        if post.status == PostStatus.DELETED:
            raise ResourceNotFoundException("게시글을 찾을 수 없습니다.")

        post.status = PostStatus.DELETED
        post.deleted_at = timezone.now()
        post.save(update_fields=["status", "deleted_at", "updated_at"])

    @staticmethod
    def _delete_comment(comment_id: int) -> None:
        try:
            comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist as exc:
            raise ResourceNotFoundException("댓글을 찾을 수 없습니다.") from exc

        if comment.status == CommentStatus.DELETED:
            raise ResourceNotFoundException("댓글을 찾을 수 없습니다.")

        comment.status = CommentStatus.DELETED
        comment.deleted_at = timezone.now()
        comment.save(update_fields=["status", "deleted_at", "updated_at"])