from django.db import models

from apps.users.models import User


class Follow(models.Model):
    follower_user_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="팔로우하는유저id",
        db_column="follower_id",
        help_text="팔로우를 하는 유저",
    )
    following_user_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="팔로우받는유저id",
        db_column="following_id",
        help_text="팔로우를 받는 유저",
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성일")

    class Meta:
        db_table = "follows"
        unique_together = ("follower_user_id", "following_user_id")  # 중복 팔로우 방지
        verbose_name = "팔로우"
        verbose_name_plural = "팔로우 목록"
