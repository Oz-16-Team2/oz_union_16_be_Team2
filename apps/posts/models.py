from django.db import models

from apps.goals.models import Goal
from apps.users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tags"

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    goal = models.ForeignKey(Goal, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_private = models.BooleanField(default=False)
    goal_start_date = models.DateTimeField(null=True, blank=True)
    goal_end_date = models.DateTimeField(null=True, blank=True)
    goal_title = models.CharField(max_length=255, null=True, blank=True)
    goal_progress = models.IntegerField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "posts"

    def __str__(self) -> str:
        return self.title


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
