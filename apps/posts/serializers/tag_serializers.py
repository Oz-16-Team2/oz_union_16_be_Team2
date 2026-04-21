from rest_framework import serializers

from apps.posts.models import Tag


class TagSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = Tag
        fields = ["id", "name"]
