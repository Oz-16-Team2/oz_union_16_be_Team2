from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ConflictException, ResourceNotFoundException
from apps.posts.models import Comment, CommentLike, Post, PostLike


class PostLikeView(APIView):
    """
    REQ-POST-007: 게시글 좋아요 API
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(summary="REQ-POST-007: 게시글 좋아요", responses={201: None}, tags=["좋아요 (Likes)"])
    def post(self, request: Request, post_id: int) -> Response:
        if not Post.objects.filter(id=post_id).exists():
            raise ResourceNotFoundException("게시글을 찾을 수 없습니다.")

        user_id = cast(int, request.user.id)

        like, created = PostLike.objects.get_or_create(user_id=user_id, post_id=post_id)

        if not created:
            raise ConflictException("이미 좋아요를 누른 게시글입니다.")

        return Response(status=status.HTTP_201_CREATED)

    @extend_schema(summary="게시글 좋아요 취소", responses={204: None}, tags=["좋아요 (Likes)"])
    def delete(self, request: Request, post_id: int) -> Response:
        user_id = cast(int, request.user.id)

        deleted, _ = PostLike.objects.filter(user_id=user_id, post_id=post_id).delete()

        if not deleted:
            raise ResourceNotFoundException("좋아요 기록을 찾을 수 없습니다.")

        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentLikeView(APIView):
    """
    REQ-COMM-004: 댓글 좋아요 API
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(summary="REQ-COMM-004: 댓글 좋아요", responses={201: None}, tags=["좋아요 (Likes)"])
    def post(self, request: Request, comment_id: int) -> Response:
        # 삭제된 댓글이나 존재하지 않는 댓글 방어
        if not Comment.objects.filter(id=comment_id, deleted_at__isnull=True).exists():
            raise ResourceNotFoundException("댓글을 찾을 수 없습니다.")

        user_id = cast(int, request.user.id)

        like, created = CommentLike.objects.get_or_create(user_id=user_id, comment_id=comment_id)
        if not created:
            raise ConflictException("이미 좋아요를 누른 댓글입니다.")

        return Response(status=status.HTTP_201_CREATED)

    @extend_schema(summary="댓글 좋아요 취소", responses={204: None}, tags=["좋아요 (Likes)"])
    def delete(self, request: Request, comment_id: int) -> Response:
        user_id = cast(int, request.user.id)

        deleted, _ = CommentLike.objects.filter(user_id=user_id, comment_id=comment_id).delete()

        if not deleted:
            raise ResourceNotFoundException("좋아요 기록을 찾을 수 없습니다.")

        return Response(status=status.HTTP_204_NO_CONTENT)
