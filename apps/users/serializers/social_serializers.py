from typing import Any

from rest_framework import serializers


class SocialLoginSerializer(serializers.Serializer[Any]):
    code = serializers.CharField()
    state = serializers.CharField(required=False, allow_blank=True, default="")
