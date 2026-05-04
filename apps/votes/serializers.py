from __future__ import annotations

from typing import Any

from django.utils import timezone
from rest_framework import serializers

from apps.core.choices import VoteStatus


class VoteOptionDetailSerializer(serializers.Serializer[Any]):
    vote_option_id = serializers.IntegerField()
    content = serializers.CharField()
    sort_order = serializers.IntegerField()


class VoteCreateRequestSerializer(serializers.Serializer[Any]):
    options = serializers.ListField(child=serializers.CharField(max_length=255), min_length=2, max_length=2)
    end_at = serializers.DateTimeField()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs.get("end_at") and attrs["end_at"] <= timezone.now():
            raise serializers.ValidationError("종료 시간은 현재 시간 이후여야 합니다.")
        return attrs

    def validate_options(self, value: list[str]) -> list[str]:
        stripped = [option.strip() for option in value]
        if any(not option for option in stripped):
            raise serializers.ValidationError("투표 입력값이 올바르지 않습니다.")
        return stripped


class VoteCreateResponseSerializer(serializers.Serializer[Any]):
    vote_id = serializers.IntegerField()
    post_id = serializers.IntegerField()
    start_at = serializers.DateField(format="%Y-%m-%d")
    end_at = serializers.DateField(format="%Y-%m-%d")
    status = serializers.ChoiceField(choices=VoteStatus.choices)
    options = VoteOptionDetailSerializer(many=True)


class VoteParticipateSerializer(serializers.Serializer[Any]):
    vote_option_id = serializers.IntegerField()


class VoteParticipateResponseSerializer(serializers.Serializer[Any]):
    vote_id = serializers.IntegerField()
    vote_option_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class VoteUpdateSerializer(serializers.Serializer[Any]):
    options = serializers.ListField(
        child=serializers.CharField(max_length=255),
        min_length=2,
        max_length=2,
    )
    end_at = serializers.DateTimeField()
    is_ended = serializers.BooleanField(required=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs.get("end_at") and attrs["end_at"] <= timezone.now():
            raise serializers.ValidationError("종료 시간은 현재 시간 이후여야 합니다.")
        return attrs


class VoteUpdateResponseSerializer(serializers.Serializer[Any]):
    vote_id = serializers.IntegerField()
    start_at = serializers.DateTimeField(format="%Y-%m-%d")
    end_at = serializers.DateTimeField(format="%Y-%m-%d")
    status = serializers.ChoiceField(choices=VoteStatus.choices)
    options = VoteOptionDetailSerializer(many=True)


class VoteDeleteResponseSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField(required=False)


class VoteResultOptionSerializer(serializers.Serializer[Any]):
    vote_option_id = serializers.IntegerField()
    content = serializers.CharField(max_length=255)
    count = serializers.IntegerField(min_value=0)
    rate = serializers.FloatField(min_value=0.0)


class VoteDetailSerializer(serializers.Serializer[Any]):
    vote_id = serializers.IntegerField()
    status = serializers.CharField()
    total_count = serializers.IntegerField(min_value=0)
    options = VoteResultOptionSerializer(many=True)
    is_voted = serializers.BooleanField()
    voted_option_id = serializers.IntegerField(allow_null=True, required=False)
