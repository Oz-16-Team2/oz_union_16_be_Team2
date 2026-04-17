from __future__ import annotations

from typing import Any

from rest_framework import serializers


class PostLikeSerializer(serializers.Serializer[Any]):
    post_id = serializers.IntegerField()


class PostLikeResponseSerializer(serializers.Serializer[Any]):
    is_liked = serializers.BooleanField()
