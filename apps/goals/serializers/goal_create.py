from datetime import date
from typing import Any

from rest_framework import serializers

from apps.goals.models import Goal


class GoalSerializer(serializers.ModelSerializer):  # type: ignore
    startDate = serializers.DateField(source="start_date")
    endDate = serializers.DateField(source="end_date")
    goal_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = Goal
        fields = ["goal_id", "title", "startDate", "endDate", "status", "created_at"]
        read_only_fields = ["goal_id", "status", "created_at"]

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        start: date | None = data.get("start_date")
        end: date | None = data.get("end_date")

        if start is not None and end is not None:
            if start > end:
                raise serializers.ValidationError({"startDate": "종료일은 시작일보다 빠를 수 없습니다."})
        return data
