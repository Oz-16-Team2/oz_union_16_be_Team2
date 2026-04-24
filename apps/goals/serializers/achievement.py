from __future__ import annotations

from typing import Any

from rest_framework import serializers


class AchievementDaySerializer(serializers.Serializer[Any]):
    date = serializers.DateField()
    check_count = serializers.IntegerField()


class AchievementResponseSerializer(serializers.Serializer[Any]):
    start = serializers.DateField()
    end = serializers.DateField()
    days = AchievementDaySerializer(many=True)


class AchievementQuerySerializer(serializers.Serializer[Any]):
    start = serializers.DateField()
    end = serializers.DateField()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["start"] > attrs["end"]:
            raise serializers.ValidationError("start는 end보다 이전이어야 합니다.")
        return attrs
