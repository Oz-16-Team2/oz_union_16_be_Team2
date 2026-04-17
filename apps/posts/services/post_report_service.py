from __future__ import annotations

from typing import Any

from rest_framework.exceptions import NotFound, ValidationError

from apps.posts.models import Post
from apps.reports.models import Report


def create_post_report(*, user: Any, post_id: int, reason_type: str, reason_detail: str | None) -> Report:

    if not Post.objects.filter(id=post_id).exists():
        raise NotFound({"postId": ["신고하려는 게시글을 찾을 수 없습니다."]})

    if Report.objects.filter(user_id=user.id, target_id=post_id, target_type="POST").exists():
        raise ValidationError({"detail": ["이미 신고한 게시글입니다."]})

    report = Report.objects.create(
        user_id=user.id,
        target_id=post_id,
        target_type="POST",
        reason_type=reason_type,
        reason_detail=reason_detail or "",
        status="PENDING",
    )

    return report
