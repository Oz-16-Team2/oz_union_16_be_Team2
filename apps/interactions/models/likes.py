from django.db import models

from apps.posts.models import Post
from apps.users.models import User

from .comments import Comment


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes", db_column="post_id")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="post_likes", db_column="user_id")
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성일")

    class Meta:
        db_table = "post_likes"
        unique_together = ("post", "user")  # 좋아요 중복 방지
        verbose_name = "게시글 좋아요"
        verbose_name_plural = "게시글 좋아요 목록"


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
        unique_together = ("comment", "user")  # 좋아요 중복 방지
        verbose_name = "댓글 좋아요"
        verbose_name_plural = "댓글 좋아요 목록"
