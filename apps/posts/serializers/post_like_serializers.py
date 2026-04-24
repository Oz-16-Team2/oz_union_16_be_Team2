from __future__ import annotations

from typing import Any

from rest_framework import serializers


class PostLikeResponseSerializer(serializers.Serializer[Any]):
    is_liked = serializers.BooleanField()
    detail = serializers.CharField()
