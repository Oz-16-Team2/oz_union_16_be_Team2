from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.posts.models import Tag


class AdminTagListQuerySerializer(serializers.Serializer[dict[str, Any]]):
    page = serializers.IntegerField(min_value=1)
    size = serializers.IntegerField(min_value=1)


class AdminTagCreateRequestSerializer(serializers.Serializer[dict[str, Any]]):
    name = serializers.CharField(max_length=100)


class AdminTagUpdateRequestSerializer(serializers.Serializer[dict[str, Any]]):
    is_active = serializers.BooleanField()


class AdminTagResponseSerializer(serializers.ModelSerializer[Tag]):
    class Meta:
        model = Tag
        fields = (
            "id",
            "name",
            "is_active",
            "created_at",
        )


class AdminTagListSuccessResponseSerializer(serializers.Serializer[dict[str, Any]]):
    detail = AdminTagResponseSerializer(many=True)


class AdminTagMessageResponseSerializer(serializers.Serializer[dict[str, Any]]):
    detail = serializers.CharField()
