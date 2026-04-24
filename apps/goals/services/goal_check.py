from __future__ import annotations

import datetime
from typing import Any

from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.core.choices import Status
from apps.goals.models import CheckGoal, Goal, Ranking


def recalculate_ranks(week_start: datetime.date, month_start: datetime.date) -> None:
    weekly_rankings = Ranking.objects.filter(week_start=week_start).order_by("-weekly_cert_count")
    for idx, r in enumerate(weekly_rankings, start=1):
        Ranking.objects.filter(pk=r.pk).update(weekly_rank=idx)

    monthly_rankings = Ranking.objects.filter(month_start=month_start).order_by("-monthly_cert_count")
    for idx, r in enumerate(monthly_rankings, start=1):
        Ranking.objects.filter(pk=r.pk).update(monthly_rank=idx)

    total_rankings = Ranking.objects.order_by("-total_cert_count")
    for idx, r in enumerate(total_rankings, start=1):
        Ranking.objects.filter(pk=r.pk).update(total_rank=idx)


class GoalCheckService:
    @staticmethod
    @transaction.atomic
    def check_goal_today(goal_id: int, user: Any) -> dict[str, Any]:
        goal = get_object_or_404(Goal, id=goal_id, user=user)

        now = timezone.now()
        today = timezone.localdate()

        if not (goal.start_date <= today <= goal.end_date):
            raise ValueError("목표 기간이 아닙니다.")

        if goal.checks.filter(created_at__date=today).exists():
            raise ValueError("오늘 이미 인증을 완료했습니다.")

        CheckGoal.objects.create(goal=goal, user=user)

        this_week_start = today - datetime.timedelta(days=today.weekday())
        this_month_start = today.replace(day=1)

        ranking, _ = Ranking.objects.get_or_create(
            user=user,
            defaults={
                "week_start": this_week_start,
                "month_start": this_month_start,
                "weekly_cert_count": 0,
                "monthly_cert_count": 0,
                "total_cert_count": 0,
                "calculated_at": now,
            },
        )

        if ranking.week_start != this_week_start:
            ranking.week_start = this_week_start
            ranking.weekly_cert_count = 1
        else:
            ranking.weekly_cert_count = F("weekly_cert_count") + 1

        if ranking.month_start != this_month_start:
            ranking.month_start = this_month_start
            ranking.monthly_cert_count = 1
        else:
            ranking.monthly_cert_count = F("monthly_cert_count") + 1

        ranking.total_cert_count = F("total_cert_count") + 1
        ranking.calculated_at = now
        ranking.save()

        recalculate_ranks(this_week_start, this_month_start)

        delta = goal.end_date - goal.start_date
        target_count = max(0, delta.days + 1)
        current_count = goal.checks.count()

        progress_rate = 0.0
        if target_count > 0:
            progress_rate = round((current_count / target_count) * 100, 1)

        if progress_rate >= 100:
            goal.status = Status.COMPLETED
            goal.save(update_fields=["status"])
        elif today == goal.end_date and progress_rate < 100:
            goal.status = Status.FAILED
            goal.save(update_fields=["status"])

        return {"detail": "오늘의 목표 달성 인증이 완료되었습니다.", "goal_id": goal.id, "progress_rate": progress_rate}
