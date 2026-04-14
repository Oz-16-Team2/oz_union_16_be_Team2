from datetime import date
from typing import Any

from django.shortcuts import get_object_or_404

from apps.core.choices import Status
from apps.goals.models import Goal


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
