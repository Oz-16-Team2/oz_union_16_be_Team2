from django.db import models

from apps.posts.models import Post
from apps.users.models import User


class Scrap(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="scraps", db_column="post_id")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scraps", db_column="user_id")
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성 시각")

    class Meta:
        db_table = "scraps"
        unique_together = ("post", "user")  # 스크랩 중복 방지
        verbose_name = "스크랩"
        verbose_name_plural = "스크랩 목록"
