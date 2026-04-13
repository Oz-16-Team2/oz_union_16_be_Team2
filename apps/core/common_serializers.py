from typing import Any

from rest_framework import serializers


class DetailMessageSerializer(serializers.Serializer[dict[str, Any]]):
    detail = serializers.CharField()


class ErrorDetailStringSerializer(serializers.Serializer[dict[str, Any]]):
    error_detail = serializers.CharField()
