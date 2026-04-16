from datetime import date
from typing import Any

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.core.choices import Status
from apps.goals.models import CheckGoal, Goal


class GoalCreateService:
    @staticmethod
    def create_goal(user: Any, title: str, start_date: date, end_date: date) -> Goal:
        goal = Goal.objects.create(
            user=user, title=title, start_date=start_date, end_date=end_date, status=Status.IN_PROGRESS
        )
        return goal

    @staticmethod
    def get_goal(goal_id: int, user: Any) -> Goal:
        return get_object_or_404(Goal, id=goal_id, user=user)

    @staticmethod
    def update_goal(goal: Goal, **update_data: Any) -> Goal:
        if goal.status != Status.IN_PROGRESS:
            raise PermissionError("진행 중인 목표만 수정할 수 있습니다.")

        for attr, value in update_data.items():
            setattr(goal, attr, value)

        goal.save()
        return goal

    @staticmethod
    def delete_goal(goal: Goal) -> None:
        goal.delete()

    @staticmethod
    @transaction.atomic
    def check_goal_today(goal_id: int, user: Any) -> dict[str, Any]:
        goal = get_object_or_404(Goal, id=goal_id, user=user)
        today = timezone.now().date()

        if not (goal.start_date <= today <= goal.end_date):
            raise ValueError("목표 기간이 아닙니다.")

        if goal.checks.filter(created_at__date=today).exists():
            raise ValueError("오늘 이미 인증을 완료했습니다.")

        CheckGoal.objects.create(goal=goal, user=user)

        delta = goal.end_date - goal.start_date
        target_count = max(0, delta.days + 1)
        current_count = goal.checks.count()

        progress_rate = 0.0
        if target_count > 0:
            progress_rate = round((current_count / target_count) * 100, 1)

        return {
            "detail": "오늘의 목표 달성 인증이 완료되었습니다.",
            "goal_id": goal.id,
            "progress_rate": progress_rate,
        }
