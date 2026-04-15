from typing import Any

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.choices import CommentStatus, PostStatus
from apps.goals.models import Goal
from apps.users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성 시각")

    class Meta:
        db_table = "tags"
        verbose_name = "태그"
        verbose_name_plural = "태그 목록"

    def __str__(self) -> str:
        return self.name


def image_count(value: Any) -> None:
    if len(value) > 3:
        raise ValidationError("이미지는 최대 3개까지만 등록 가능합니다.")


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    goal = models.ForeignKey(Goal, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    title = models.CharField(max_length=255)
    content = models.TextField()
    images = models.JSONField(default=list, validators=[image_count], help_text="게시글 이미지 URL 리스트(최대 3개)")
    is_private = models.BooleanField(default=False)
    goal_start_date = models.DateTimeField(null=True, blank=True)
    goal_end_date = models.DateTimeField(null=True, blank=True)
    goal_title = models.CharField(max_length=255, null=True, blank=True)
    goal_progress = models.IntegerField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=PostStatus, default=PostStatus.NORMAL)

    class Meta:
        db_table = "posts"

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments", db_column="post")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments", db_column="user")
    content = models.CharField(max_length=500, help_text="댓글 내용")
    status = models.CharField(
        max_length=20,
        choices=CommentStatus.choices,
        default=CommentStatus.ACTIVE,
        help_text="상태(활성, 비활성화)",
    )

    deleted_at = models.DateTimeField(null=True, blank=True, help_text="삭제일")
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성일")
    updated_at = models.DateTimeField(auto_now=True, help_text="수정일")

    class Meta:
        db_table = "comments"
        verbose_name = "댓글"
        verbose_name_plural = "댓글 목록"

    def __str__(self) -> str:
        return f"{self.user.nickname}: {self.content[:20]}"


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="post_likes")
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성일")

    class Meta:
        db_table = "post_likes"
        unique_together = ("post", "user")
        verbose_name = "게시글 좋아요"
        verbose_name_plural = "게시글 좋아요 목록"


class CommentLike(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comment_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "comment_likes"
        unique_together = ("comment", "user")
        verbose_name = "댓글 좋아요"
        verbose_name_plural = "댓글 좋아요 목록"


class PostView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="post_views", verbose_name="조회 유저")
    post = models.ForeignKey("Post", on_delete=models.CASCADE, related_name="view_logs", verbose_name="조회 게시글")
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name="조회 일시")

    class Meta:
        db_table = "post_views"
        verbose_name = "게시글 조회 기록"
        ordering = ["-viewed_at"]

    def __str__(self) -> str:
        return f"{self.user} - {self.post.title} ({self.viewed_at})"


class PostTag(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_tags")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="post_tags")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "post_tags"
        unique_together = ("post", "tag")


class Scrap(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="scraps")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scraps")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "scraps"
        unique_together = ("post", "user")
