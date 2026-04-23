from datetime import datetime
from typing import Any

from django.utils import timezone
from rest_framework import serializers


class DetailMessageSerializer(serializers.Serializer[dict[str, Any]]):
    detail = serializers.CharField()


class ErrorDetailStringSerializer(serializers.Serializer[dict[str, Any]]):
    error_detail = serializers.CharField()


KST = timezone.get_fixed_timezone(9 * 60)


class KSTDateTimeField(serializers.DateTimeField):
    def to_representation(self, value: datetime) -> str:
        value = timezone.localtime(value, KST)
        return value.isoformat()
