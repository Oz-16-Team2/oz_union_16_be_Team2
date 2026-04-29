import logging
from typing import Any, cast

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core import detail_response, error_response
from apps.posts.models import Post, PostLike, PostTag, Scrap
from apps.posts.serializers.post_serializers import PostListQuerySerializer, PostSuggestionResponseSerializer
from apps.posts.services.post_suggestion_service import get_recommended_posts
from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import User

logger = logging.getLogger(__name__)

_DEFAULT_PAGE_SIZE = 8
_CONTENT_PREVIEW_LENGTH = 100


def _build_suggestion_items(posts: list[Post], user: User) -> list[dict[str, Any]]:
    if not posts:
        return []

    post_ids = [p.pk for p in posts]

    tag_map: dict[int, list[str]] = {pid: [] for pid in post_ids}
    for pt in PostTag.objects.filter(post_id__in=post_ids).select_related("tag").order_by("post_id", "id"):
        tag_map[pt.post_id].append(pt.tag.name)

    scrapped_ids = set(Scrap.objects.filter(post_id__in=post_ids, user=user).values_list("post_id", flat=True))
    liked_ids = set(PostLike.objects.filter(post_id__in=post_ids, user=user).values_list("post_id", flat=True))

    items: list[dict[str, Any]] = []
    for p in posts:
        preview = p.content[:_CONTENT_PREVIEW_LENGTH] if p.content else ""
        items.append(
            {
                "post_id": p.id,
                "images": p.images or [],
                "profile_image_url": PROFILE_IMAGE_URL_MAP.get(p.user.profile_image),
                "nickname": p.user.nickname,
                "created_at": p.created_at,
                "title": p.title,
                "tags": tag_map.get(p.pk, []),
                "content_preview": preview,
                "like_count": p.likes.count(),
                "comment_count": p.comments.count(),
                "is_liked": p.pk in liked_ids,
                "is_scrapped": p.pk in scrapped_ids,
            }
        )
    return items


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

            recommended_posts, total_count = get_recommended_posts(user=user, page=page + 1, size=size)

            return detail_response(
                {
                    "posts": _build_suggestion_items(recommended_posts, user),
                    "page": page,
                    "size": size,
                    "total_count": total_count,
                },
                status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"[Suggestion Error] User {request.user.id} 추천 실패: {str(e)}")
            return error_response(
                {"server_error": ["추천 피드를 불러오는 중 문제가 발생했습니다."]},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
