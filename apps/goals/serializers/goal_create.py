from datetime import date
from typing import Any

from rest_framework import serializers

from apps.goals.models import Goal


class GoalCreateSerializer(serializers.ModelSerializer[Any]):
    startDate = serializers.DateField(source="start_date", help_text="2026-04-14", initial=date(2026, 4, 14))
    endDate = serializers.DateField(source="end_date", help_text="2026-04-15", initial=date(2026, 4, 15))
    title = serializers.CharField(help_text="목표 제목을 입력하세요", initial="매일 물 2L 마시기")

    class Meta:
        model = Goal
        fields = ["title", "startDate", "endDate"]

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        start: date | None = data.get("start_date")
        end: date | None = data.get("end_date")
        if start and end and start > end:
            raise serializers.ValidationError({"startDate": "종료일은 시작일보다 빠를 수 없습니다."})
        return data


class GoalReadSerializer(serializers.ModelSerializer[Any]):
    startDate = serializers.DateField(source="start_date")
    endDate = serializers.DateField(source="end_date")
    goal_id = serializers.IntegerField(source="id")

    class Meta:
        model = Goal
        fields = ["goal_id", "title", "startDate", "endDate", "status", "created_at"]


class GoalUpdateSerializer(serializers.ModelSerializer[Any]):
    startDate = serializers.DateField(
        source="start_date",
        required=False,
    )
    endDate = serializers.DateField(
        source="end_date",
        required=False,
    )
    title = serializers.CharField(required=False, default="수정된 목표 제목")

    class Meta:
        model = Goal
        fields = ["title", "startDate", "endDate"]


class ErrorDetailSerializer(serializers.Serializer[dict[str, Any]]):
    error_detail = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()), help_text="필드별 에러 메시지 리스트"
    )
