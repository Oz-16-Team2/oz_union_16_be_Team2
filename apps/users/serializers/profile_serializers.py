from typing import Any

from rest_framework import serializers

from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import User


class UserProfileSerializer(serializers.ModelSerializer[Any]):
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "nickname", "profile_image_url"]

    def get_profile_image_url(self, obj: User) -> str:
        return PROFILE_IMAGE_URL_MAP.get(obj.profile_image, "")


class MeActivitySummaryDaysDetailSerializer(serializers.Serializer[Any]):
    days_together = serializers.IntegerField()


class MeActivitySummaryDaysResponseSerializer(serializers.Serializer[Any]):
    detail = MeActivitySummaryDaysDetailSerializer()


class MeActivitySummaryAchievementRateDetailSerializer(serializers.Serializer[Any]):
    total_goals_count = serializers.IntegerField()
    completed_goals_count = serializers.IntegerField()
    total_achievement_rate = serializers.FloatField()


class MeActivitySummaryAchievementRateResponseSerializer(serializers.Serializer[Any]):
    detail = MeActivitySummaryAchievementRateDetailSerializer()


class MeActivitySummaryCompletedGoalsDetailSerializer(serializers.Serializer[Any]):
    completed_goals_count = serializers.IntegerField()


class MeActivitySummaryCompletedGoalsResponseSerializer(serializers.Serializer[Any]):
    detail = MeActivitySummaryCompletedGoalsDetailSerializer()
