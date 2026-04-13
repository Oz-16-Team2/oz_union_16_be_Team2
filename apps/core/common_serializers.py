from rest_framework import serializers


class DetailMessageSerializer(serializers.Serializer):  # type: ignore[misc]
    detail = serializers.CharField()


class ErrorDetailStringSerializer(serializers.Serializer):  # type: ignore[misc]
    error_detail = serializers.CharField()
