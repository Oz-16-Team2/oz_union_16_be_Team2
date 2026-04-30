import logging
from typing import cast

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core import detail_response, error_response
from apps.posts.serializers.post_serializers import PostListQuerySerializer, PostSuggestionResponseSerializer
from apps.posts.services.post_suggestion_service import get_recommendation_feed
from apps.users.models import User

logger = logging.getLogger(__name__)

_DEFAULT_PAGE_SIZE = 8


class PostSuggestionAPIView(APIView):
    """맞춤형 추천 게시글 조회: 유저의 활동(작성, 좋아요)을 분석하여 맞춤형 게시글을 추천"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="맞춤형 추천 게시글 조회",
        description=(
            "현재 로그인한 유저의 최근 활동(게시글 작성, 좋아요)을 기반으로 맞춤형 게시글을 추천합니다.<br>"
            "- 결과는 페이지당 8개.<br>"
            "- 활동 데이터가 부족한 신규 유저의 경우 최신글이 대체 제공됩니다."
        ),
        parameters=[
            OpenApiParameter(
                name="page",
                type=int,
                location=OpenApiParameter.QUERY,
                description="페이지 번호 (0부터 시작)",
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
        tags=["추천 (Suggestions)"],
        responses={
            200: PostSuggestionResponseSerializer,
            400: dict,
            401: dict,
            500: dict,
        },
    )
    def get(self, request: Request) -> Response:
        try:
            user = cast(User, request.user)

            query_serializer = PostListQuerySerializer(data=request.query_params)
            if not query_serializer.is_valid():
                return error_response(query_serializer.errors, status.HTTP_400_BAD_REQUEST)

            page: int = query_serializer.validated_data.get("page", 0)
            size: int = query_serializer.validated_data.get("size", _DEFAULT_PAGE_SIZE)

            data = get_recommendation_feed(user=user, page=page, size=size)
            response_serializer = PostSuggestionResponseSerializer(instance=data)
            return detail_response(response_serializer.data, status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[Suggestion Error] User {getattr(request.user, 'id', None)} 추천 실패: {str(e)}")
            return error_response(
                {"server_error": ["추천 피드를 불러오는 중 문제가 발생했습니다."]},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
