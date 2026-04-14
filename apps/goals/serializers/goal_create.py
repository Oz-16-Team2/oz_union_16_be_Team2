from datetime import date
from typing import Any

from django.utils import timezone
from rest_framework import serializers

from apps.goals.models import Goal


class GoalCreateSerializer(serializers.ModelSerializer[Any]):
    startDate = serializers.DateField(source="start_date", help_text="2026-04-14", initial=date(2026, 4, 14))
    endDate = serializers.DateField(source="end_date", help_text="2026-05-14", initial=date(2026, 5, 14))
    title = serializers.CharField(help_text="목표 제목을 입력하세요", initial="매일 물 2L 마시기")

    class Meta:
        model = Goal
        fields = ["title", "startDate", "endDate"]

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        start: date | None = data.get("start_date")
        end: date | None = data.get("end_date")
        if start and end and start > end:
            raise serializers.ValidationError({"startDate": ["종료일은 시작일보다 빠를 수 없습니다."]})
        return data


class GoalReadSerializer(serializers.ModelSerializer[Any]):
    startDate = serializers.DateField(source="start_date")
    endDate = serializers.DateField(source="end_date")
    goal_id = serializers.IntegerField(source="id")
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S")
    currentCount = serializers.SerializerMethodField()
    targetCount = serializers.SerializerMethodField()
    progressRate = serializers.SerializerMethodField()
    isCheckedToday = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = [
            "goal_id",
            "title",
            "startDate",
            "endDate",
            "status",
            "created_at",
            "currentCount",
            "targetCount",
            "progressRate",
            "isCheckedToday",
        ]

    def get_currentCount(self, obj: Goal) -> int:
        return obj.checks.count()

    def get_targetCount(self, obj: Goal) -> int:
        delta = obj.end_date - obj.start_date
        return max(0, delta.days + 1)

    def get_progressRate(self, obj: Goal) -> float:
        target = self.get_targetCount(obj)
        current = self.get_currentCount(obj)
        if target <= 0:
            return 0.0
        return round((current / target) * 100, 1)

    def get_isCheckedToday(self, obj: Goal) -> bool:
        today = timezone.now().date()
        return obj.checks.filter(created_at__date=today).exists()


class GoalUpdateSerializer(serializers.ModelSerializer[Any]):
    startDate = serializers.DateField(source="start_date", required=False)
    endDate = serializers.DateField(source="end_date", required=False)
    title = serializers.CharField(required=False)

    class Meta:
        model = Goal
        fields = ["title", "startDate", "endDate"]

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        start = data.get("start_date") or (self.instance.start_date if self.instance else None)
        end = data.get("end_date") or (self.instance.end_date if self.instance else None)

        if start and end and start > end:
            raise serializers.ValidationError({"startDate": ["종료일은 시작일보다 빠를 수 없습니다."]})
        return data


class ErrorDetailSerializer(serializers.Serializer[dict[str, Any]]):
    error_detail = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()), help_text="필드별 에러 메시지 리스트"
    )
