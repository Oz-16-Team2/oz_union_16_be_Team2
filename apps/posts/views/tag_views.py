from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.models import Tag
from apps.posts.serializers.tag_serializers import TagSerializer


class TagListView(APIView):
    """
    REQ-TAG-001: 태그 검색 및 목록 조회
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="태그 목록 및 검색",
        parameters=[OpenApiParameter(name="keyword", description="검색할 태그 키워드", required=False, type=str)],
        responses=TagSerializer(many=True),
        tags=["태그 (Tags)"],
    )
    def get(self, request: Request) -> Response:
        keyword = request.query_params.get("keyword", "").strip()

        # is_active=True 인 활성 태그만 조회되게
        base_query = Tag.objects.filter(is_active=True)

        # 키워드가 있으면 포함된 태그만 필터링, 없으면 전체 최신순 조회
        if keyword:
            tags = base_query.filter(name__icontains=keyword).order_by("-created_at")[:20]  # 최대 20개 자동완성
        else:
            tags = base_query.order_by("-created_at")[:50]  # 기본 50개 노출

        serializer = TagSerializer(tags, many=True)
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)
