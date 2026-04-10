from django.db import models

from apps.core.choices import VoteStatus
from apps.posts.models import Post
from apps.users.models import User


class Vote(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name="vote")
    question = models.CharField(max_length=255)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=VoteStatus, default=VoteStatus.IN_PROGRESS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "votes"

    def __str__(self):
        return self.question


class VoteOption(models.Model):
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE, related_name="options")
    content = models.CharField(max_length=255)
    sort_order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vote_options"
        ordering = ["sort_order"]

    def __str__(self):
        return self.content


class VoteParticipation(models.Model):
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE, related_name="participations")
    vote_option = models.ForeignKey(VoteOption, on_delete=models.CASCADE, related_name="participations")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="vote_participations")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vote_participations"
        unique_together = ("vote", "user")
