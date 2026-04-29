from typing import Any

from rest_framework import serializers


class MessageResponseSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField()


class TokenResponseSerializer(serializers.Serializer[Any]):
    access_token = serializers.CharField()


class EmailVerificationSuccessSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField()
    email_token = serializers.CharField()


class ErrorDetailFieldListSerializer(serializers.Serializer[Any]):
    error_detail = serializers.DictField(child=serializers.ListField(child=serializers.CharField()))


class ErrorDetailStringSerializer(serializers.Serializer[Any]):
    error_detail = serializers.CharField()


class WithdrawnAccountErrorDetailSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField()
    expire_at = serializers.CharField()


class ErrorDetailWithdrawnSerializer(serializers.Serializer[Any]):
    error_detail = WithdrawnAccountErrorDetailSerializer()
