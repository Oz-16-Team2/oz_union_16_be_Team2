from __future__ import annotations

from typing import Any

from rest_framework import serializers


class WeeklyRankingSerializer(serializers.Serializer[Any]):
    user_id = serializers.IntegerField()
    nickname = serializers.CharField()
    profile_img_url = serializers.CharField()
    rank = serializers.IntegerField()
    week_cert_count = serializers.IntegerField()


class MonthlyRankingSerializer(serializers.Serializer[Any]):
    user_id = serializers.IntegerField()
    nickname = serializers.CharField()
    profile_img_url = serializers.CharField()
    rank = serializers.IntegerField()
    month_cert_count = serializers.IntegerField()


class TotalRankingSerializer(serializers.Serializer[Any]):
    user_id = serializers.IntegerField()
    nickname = serializers.CharField()
    profile_img_url = serializers.CharField()
    rank = serializers.IntegerField()
    total_cert_count = serializers.IntegerField()


class WeeklyRankingResponseSerializer(serializers.Serializer[Any]):
    rankings = WeeklyRankingSerializer(many=True)


class MonthlyRankingResponseSerializer(serializers.Serializer[Any]):
    rankings = MonthlyRankingSerializer(many=True)


class TotalRankingResponseSerializer(serializers.Serializer[Any]):
    rankings = TotalRankingSerializer(many=True)
