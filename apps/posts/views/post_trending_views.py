from __future__ import annotations

from typing import Any, cast

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ResourceNotFoundException
from apps.core.response import detail_response, error_response
from apps.posts.serializers.post_serializers import PostSuggestionResponseSerializer
from apps.posts.services.post_trending_service import DEFAULT_PERIOD, PERIOD_DAYS, get_trending_posts
from apps.users.models import User


class _TrendingQuerySerializer(serializers.Serializer[Any]):
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=8)
    period = serializers.ChoiceField(
        choices=list(PERIOD_DAYS.keys()),
        required=False,
        default=DEFAULT_PERIOD,
        help_text="day=지금 핫한 글(24h), week=요즘 뜨는 글(7일)",
    )


class PostTrendingAPIView(APIView):
    """인기순 추천 — 요즘 뜨는 글 / 지금 핫한 글"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="인기 게시글 조회",
        description=(
            "최근 기간 내 좋아요 수 기준 인기 게시글을 반환합니다.<br>"
            "- <b>period=day</b>: 지금 핫한 글 (최근 24시간)<br>"
            "- <b>period=week</b>: 요즘 뜨는 글 (최근 7일, 기본값)"
        ),
        parameters=[
            OpenApiParameter(
                name="period", type=str, location=OpenApiParameter.QUERY, description="day | week", required=False
            ),
            OpenApiParameter(
                name="page",
                type=int,
                location=OpenApiParameter.QUERY,
                description="페이지 번호 (1부터 시작)",
                required=False,
            ),
            OpenApiParameter(
                name="size",
                type=int,
                location=OpenApiParameter.QUERY,
                description="페이지 크기 (기본: 8)",
                required=False,
            ),
        ],
        tags=["게시글 (Posts)"],
        responses={
            200: PostSuggestionResponseSerializer,
            400: dict,
            401: dict,
        },
    )
    def get(self, request: Request) -> Response:
        query_serializer = _TrendingQuerySerializer(data=request.query_params)
        if not query_serializer.is_valid():
            return error_response(query_serializer.errors, status.HTTP_400_BAD_REQUEST)

        user = cast(User, request.user)
        try:
            data = get_trending_posts(
                user=user,
                page=query_serializer.validated_data["page"],
                size=query_serializer.validated_data["size"],
                period=query_serializer.validated_data["period"],
            )
        except ResourceNotFoundException as e:
            return error_response(e.detail, status.HTTP_404_NOT_FOUND)

        response_serializer = PostSuggestionResponseSerializer(instance=data)
        return detail_response(response_serializer.data, status.HTTP_200_OK)
