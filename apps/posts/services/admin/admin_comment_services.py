from __future__ import annotations

from django.utils import timezone

from apps.core.choices import CommentStatus
from apps.core.exceptions import ResourceNotFoundException
from apps.posts.models import Comment


class AdminCommentService:
    @staticmethod
    def delete_comment(*, comment_id: int) -> None:
        try:
            comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist as exc:
            raise ResourceNotFoundException("댓글을 찾을 수 없습니다.") from exc

        if comment.status == CommentStatus.DELETED:
            raise ResourceNotFoundException("댓글을 찾을 수 없습니다.")

        comment.status = CommentStatus.DELETED
        comment.deleted_at = timezone.now()
        comment.save(update_fields=["status", "deleted_at", "updated_at"])
