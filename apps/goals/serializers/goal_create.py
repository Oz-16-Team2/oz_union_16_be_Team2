from datetime import date
from typing import Any

from django.utils import timezone
from rest_framework import serializers

from apps.goals.models import Goal


class GoalCreateSerializer(serializers.ModelSerializer[Any]):
    start_date = serializers.DateField(help_text="2026-04-14", initial=date(2026, 4, 14))
    end_date = serializers.DateField(help_text="2026-05-14", initial=date(2026, 5, 14))
    title = serializers.CharField(help_text="목표 제목을 입력하세요", initial="매일 물 2L 마시기")

    class Meta:
        model = Goal
        fields = ["title", "start_date", "end_date"]

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        start: date | None = data.get("start_date")
        end: date | None = data.get("end_date")
        if start and end and start > end:
            raise serializers.ValidationError({"start_date": ["종료일은 시작일보다 빠를 수 없습니다."]})
        return data


class GoalReadSerializer(serializers.ModelSerializer[Any]):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    goal_id = serializers.IntegerField(source="id")
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S")
    progress_rate = serializers.SerializerMethodField()
    is_checked_today = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = [
            "goal_id",
            "title",
            "start_date",
            "end_date",
            "status",
            "created_at",
            "progress_rate",
            "is_checked_today",
        ]

    def get_progress_rate(self, obj: Goal) -> float:
        delta = obj.end_date - obj.start_date
        target = max(0, delta.days + 1)

        current = len(obj.checks.all())

        if target <= 0:
            return 0
        return int(round((current / target) * 100, 0))

    def get_is_checked_today(self, obj: Goal) -> bool:
        today = timezone.now().date()
        return any(check.created_at.date() == today for check in obj.checks.all())


class GoalUpdateSerializer(serializers.ModelSerializer[Any]):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    title = serializers.CharField(required=False)

    class Meta:
        model = Goal
        fields = ["title", "start_date", "end_date"]

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        start = data.get("start_date") or (self.instance.start_date if self.instance else None)
        end = data.get("end_date") or (self.instance.end_date if self.instance else None)

        if start and end and start > end:
            raise serializers.ValidationError({"start_date": ["종료일은 시작일보다 빠를 수 없습니다."]})
        return data


class ErrorDetailSerializer(serializers.Serializer[dict[str, Any]]):
    error_detail = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()), help_text="필드별 에러 메시지 리스트"
    )


class GoalCheckSerializer(serializers.Serializer[dict[str, Any]]):
    detail = serializers.CharField(help_text="결과 메시지")
    goal_id = serializers.IntegerField(help_text="목표 고유 ID")
    progress_rate = serializers.FloatField(help_text="현재 달성률")
