from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="태그명 (예: 미라클모닝)")
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성일")
    is_active = models.BooleanField(default=True, help_text="태그 활성화 여부")

    class Meta:
        db_table = "tags"
        verbose_name = "태그"
        verbose_name_plural = "태그 목록"

    def __str__(self):
        return self.name
