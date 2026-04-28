from django.db import models

from apps.core.choices import Status
from apps.users.models import User


class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="goals")
    title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status, default=Status.IN_PROGRESS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "goals"

    def __str__(self) -> str:
        return self.title


class CheckGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="check_goals")
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="checks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "check_goals"

    def __str__(self) -> str:
        return f"{self.user.nickname} - {self.goal.title}"


class Ranking(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="ranking")
    weekly_rank = models.IntegerField(null=True, blank=True)
    weekly_cert_count = models.IntegerField(null=True, blank=True)
    monthly_rank = models.IntegerField(null=True, blank=True)
    monthly_cert_count = models.IntegerField(null=True, blank=True)
    total_rank = models.IntegerField(null=True, blank=True)
    total_cert_count = models.IntegerField(null=True, blank=True)
    total_goal_count = models.IntegerField(null=True, blank=True)
    week_start = models.DateField(null=True, blank=True)
    month_start = models.DateField(null=True, blank=True)
    calculated_at = models.DateTimeField()

    class Meta:
        db_table = "rankings"

    def __str__(self) -> str:
        return f"{self.user.nickname} 랭킹"
