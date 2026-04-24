from typing import Any, cast

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core import detail_response, error_response
from apps.posts.models import Post, PostTag, Scrap, Tag
from apps.posts.serializers.post_serializers import PostSuggestionResponseSerializer
from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import User

_DEFAULT_PAGE_SIZE = 8
_CONTENT_PREVIEW_LENGTH = 100


class _TagPostQuerySerializer(serializers.Serializer[Any]):
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=_DEFAULT_PAGE_SIZE)


def _build_tag_post_items(posts: list[Post], user: User) -> list[dict[str, Any]]:
    if not posts:
        return []

    post_ids = [p.pk for p in posts]

    tag_map: dict[int, list[str]] = {pid: [] for pid in post_ids}
    for pt in PostTag.objects.filter(post_id__in=post_ids).select_related("tag").order_by("post_id", "id"):
        tag_map[pt.post_id].append(pt.tag.name)

    scrapped_ids = set(Scrap.objects.filter(post_id__in=post_ids, user=user).values_list("post_id", flat=True))

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
                "is_scrapped": p.pk in scrapped_ids,
            }
        )
    return items


class TagPostListView(APIView):
    """REQ-POST-011: 해당 태그가 쓰인 게시글 조회"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="태그별 게시글 조회",
        description="특정 태그가 사용된 게시글 목록을 최신순으로 반환합니다. 페이지당 8개.",
        parameters=[
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
        tags=["태그 (Tags)"],
        responses={
            200: PostSuggestionResponseSerializer,
            400: dict,
            404: dict,
        },
    )
    def get(self, request: Request, tag_id: int) -> Response:
        if not Tag.objects.filter(pk=tag_id, is_active=True).exists():
            return error_response({"tag": ["존재하지 않는 태그입니다."]}, status.HTTP_404_NOT_FOUND)

        query_serializer = _TagPostQuerySerializer(data=request.query_params)
        if not query_serializer.is_valid():
            return error_response(query_serializer.errors, status.HTTP_400_BAD_REQUEST)

        page: int = query_serializer.validated_data["page"]
        size: int = query_serializer.validated_data["size"]

        qs = Post.objects.filter(post_tags__tag_id=tag_id).select_related("user").distinct().order_by("-created_at")
        total_count = qs.count()
        posts = list(qs[(page - 1) * size : page * size])

        user = cast(User, request.user)
        return detail_response(
            {
                "posts": _build_tag_post_items(posts, user),
                "page": page,
                "size": size,
                "total_count": total_count,
            },
            status.HTTP_200_OK,
        )
