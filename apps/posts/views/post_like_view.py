from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.goals.serializers.goal_create import ErrorDetailSerializer
from apps.posts.models import Post
from apps.posts.serializers.post_serializers import PostLikeResponseSerializer
from apps.posts.services.post_like_service import PostLikeService


class PostLikeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Post_likes"],
        summary="게시글 좋아요 토글",
        description="로그인한 유저가 게시글에 좋아요를 남기거나 취소합니다.",
        responses={
            201: PostLikeResponseSerializer,
            204: PostLikeResponseSerializer,
            401: ErrorDetailSerializer,
            404: ErrorDetailSerializer,
        },
        examples=[
            OpenApiExample(
                "좋아요 성공 예시",
                value=True,
                response_only=True,
                status_codes=["201"],
            ),
            OpenApiExample(
                "게시글 없음 예시 (404)",
                value={"error_detail": {"postId": ["해당 게시글을 찾을 수 없습니다."]}},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    def post(self, request: Request, post_id: int) -> Response:
        if not request.user.is_authenticated:
            return Response({"detail": ["로그인이 필요합니다."]}, 401)

        try:
            is_liked = PostLikeService.toggle_like(post_id=post_id, user=request.user)

            if is_liked:
                return Response(status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Post.DoesNotExist:
            return Response({"error_detail": {"postId": ["해당 게시글을 찾을 수 없습니다."]}}, 404)
