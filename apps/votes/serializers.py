from __future__ import annotations

from datetime import date, datetime
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
    start_at = serializers.DateField(required=False)
    end_at = serializers.DateField()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        end_at = attrs.get("end_at")
        start_at = attrs.get("start_at")
        today = timezone.localdate()

        if end_at and end_at < today:
            raise serializers.ValidationError("종료일은 오늘 이후여야 합니다.")

        if start_at and end_at and end_at < start_at:
            raise serializers.ValidationError("종료일은 시작일보다 빠를 수 없습니다.")

        if not start_at:
            attrs["start_at"] = today

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
    status = serializers.CharField()
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
    start_at = serializers.DateField(required=False)
    end_at = serializers.DateField()
    is_ended = serializers.BooleanField(required=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        end_at = attrs.get("end_at")
        start_at = attrs.get("start_at")
        today = timezone.localdate()

        if end_at and end_at < today:
            raise serializers.ValidationError("종료일은 오늘 이후여야 합니다.")

        if start_at and end_at and end_at < start_at:
            raise serializers.ValidationError("종료일은 시작일보다 빠를 수 없습니다.")

        return attrs


class VoteUpdateResponseSerializer(serializers.Serializer[Any]):
    vote_id = serializers.IntegerField()
    start_at = serializers.DateField(format="%Y-%m-%d")
    end_at = serializers.DateField(format="%Y-%m-%d")
    status = serializers.CharField()
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
    status = serializers.SerializerMethodField()
    total_count = serializers.IntegerField(min_value=0)
    options = VoteResultOptionSerializer(many=True)
    is_voted = serializers.BooleanField()
    voted_option_id = serializers.IntegerField(allow_null=True, required=False)

    def get_status(self, obj: Any) -> str:
        raw_status = getattr(obj, "status", None) if not isinstance(obj, dict) else obj.get("status")
        status = raw_status.lower() if raw_status else None
        end_at = getattr(obj, "end_at", None) if not isinstance(obj, dict) else obj.get("end_at")

        if status == VoteStatus.CLOSED.value:
            return VoteStatus.CLOSED.value

        if end_at:
            now = timezone.now()
            target_end_at = end_at

            if isinstance(target_end_at, str):
                try:
                    target_end_at = datetime.fromisoformat(target_end_at.replace("Z", "+00:00"))
                except ValueError:
                    target_end_at = timezone.make_aware(datetime.strptime(target_end_at[:10], "%Y-%m-%d"))

            if isinstance(target_end_at, date) and not isinstance(target_end_at, datetime):
                if target_end_at < now.date():
                    return VoteStatus.CLOSED.value
                return VoteStatus.IN_PROGRESS.value

            if isinstance(target_end_at, datetime):
                if timezone.is_naive(target_end_at):
                    target_end_at = timezone.make_aware(target_end_at)

                if target_end_at < now:
                    return VoteStatus.CLOSED.value

        return VoteStatus.IN_PROGRESS.value
