from __future__ import annotations

from typing import Any

from rest_framework.exceptions import NotFound, ValidationError

from apps.posts.models import Comment
from apps.reports.models import Report


def create_comment_report(*, user: Any, comment_id: int, reason_type: str, reason_detail: str | None) -> Report:
    if not Comment.objects.filter(id=comment_id).exists():
        raise NotFound({"commentId": ["신고하려는 댓글을 찾을 수 없습니다."]})

    if Report.objects.filter(user_id=user.id, target_id=comment_id, target_type="comment").exists():
        raise ValidationError({"detail": ["이미 신고한 댓글입니다."]})

    return Report.objects.create(
        user_id=user.id,
        target_id=comment_id,
        target_type="comment",
        reason_type=reason_type,
        reason_detail=reason_detail or "",
        status="PENDING",
    )
