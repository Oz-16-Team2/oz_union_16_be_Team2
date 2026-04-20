from typing import Any

from rest_framework import serializers

from apps.posts.models import Scrap


class ScrapListSerializer(serializers.ModelSerializer[Any]):
    title = serializers.CharField(source="post.title", read_only=True)

    class Meta:
        model = Scrap
        fields = ["id", "post_id", "title", "created_at"]
