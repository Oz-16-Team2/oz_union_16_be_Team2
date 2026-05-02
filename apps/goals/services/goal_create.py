from datetime import date
from typing import Any

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.core.choices import Status
from apps.core.exceptions import ConflictException
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
    def get_goal_list(
        user: Any,
        status_filter: str | None = None,
        start_date_filter: str | None = None,
        end_date_filter: str | None = None,
    ) -> QuerySet[Goal]:
        today = timezone.now().date()

        expired_goals = Goal.objects.filter(user=user, status=Status.IN_PROGRESS, end_date__lt=today)
        for goal in expired_goals:
            GoalCreateService.update_goal_status(goal)

        queryset = Goal.objects.filter(user=user).prefetch_related("checks").order_by("-created_at")

        if status_filter in ["in_progress", "failed", "completed"]:
            queryset = queryset.filter(status=Status[status_filter.upper()])

        if start_date_filter:
            queryset = queryset.filter(start_date__gte=start_date_filter)

        if end_date_filter:
            queryset = queryset.filter(end_date__lte=end_date_filter)

        return queryset

    @staticmethod
    def get_checked_goals_by_date(user: Any, target_date: str) -> QuerySet[Goal]:
        return (
            Goal.objects.filter(user=user, checks__created_at__date=target_date)
            .prefetch_related("checks")
            .distinct()
            .order_by("-created_at")
        )

    @staticmethod
    def update_goal(goal: Goal, **update_data: Any) -> Goal:
        if goal.status != Status.IN_PROGRESS:
            raise ConflictException({"detail": ["진행 중인 목표만 수정할 수 있습니다."]})

        update_data.pop("start_date", None)
        update_data.pop("end_date", None)

        for attr, value in update_data.items():
            setattr(goal, attr, value)

        goal.save()
        return goal

    @staticmethod
    def delete_goal(goal: Goal) -> None:
        goal.delete()

    @staticmethod
    def update_goal_status(goal: Goal) -> None:
        today = timezone.now().date()

        if goal.end_date >= today:
            return

        delta = goal.end_date - goal.start_date
        target_count = max(0, delta.days + 1)
        current_count = goal.checks.count()

        if current_count >= target_count:
            goal.status = Status.COMPLETED
        else:
            goal.status = Status.FAILED

        goal.save()
