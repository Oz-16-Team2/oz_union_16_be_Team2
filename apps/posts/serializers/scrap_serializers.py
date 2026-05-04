from typing import Any

from rest_framework import serializers


class ScrapListQuerySerializer(serializers.Serializer[Any]):
    page = serializers.IntegerField(required=False, min_value=0, default=0)
    size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
