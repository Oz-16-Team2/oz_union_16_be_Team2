from django.db import models

from apps.core.choices import CommentStatus
from apps.posts.models import Post
from apps.users.models import User


class Comment(models.Model):
    post_id = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments", db_column="post_id")
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments", db_column="user_id")
    content = models.CharField(max_length=500, help_text="댓글 내용")
    status = models.CharField(
        max_length=20,
        choices=CommentStatus,
        default="ACTIVE",
        help_text="상태(활성, 비활성화)",
    )

    deleted_at = models.DateTimeField(null=True, blank=True, help_text="삭제일")
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성일")
    updated_at = models.DateTimeField(auto_now=True, help_text="수정일")

    class Meta:
        db_table = "comments"
        verbose_name = "댓글"
        verbose_name_plural = "댓글 목록"


class CommentLike(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes", db_column="comment_id")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comment_likes",
        db_column="user_id",
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성일")

    class Meta:
        db_table = "comment_likes"
        verbose_name = "댓글 좋아요"
        verbose_name_plural = "댓글 좋아요 목록"
