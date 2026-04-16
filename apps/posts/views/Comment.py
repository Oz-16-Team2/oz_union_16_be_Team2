from typing import Any

from django.db.models import BooleanField, Count, Exists, OuterRef, Value
from django.db.models.query import QuerySet
from rest_framework import generics

# from apps.core.exceptions import ResourceNotFoundException
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.serializers import BaseSerializer

from apps.posts.models import Comment, CommentLike, Post
from apps.posts.serializers.serializers_comment import (
    CommentCreateSerializer,
    CommentListSerializer,
)


class PostCommentListCreateView(generics.ListCreateAPIView):  # type: ignore[type-arg]
    """
    <GET> 댓글 목록 조회 View
    <POST> 댓글 작성 View
    URL: /api/v1/posts/{post_id}/comments
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self) -> type[BaseSerializer[Any]]:
        if self.request.method == "POST":
            return CommentCreateSerializer
        return CommentListSerializer

    def get_queryset(self) -> QuerySet[Comment]:
        post_id: int = self.kwargs.get("post_id")

        if not Post.objects.filter(id=post_id).exists():
            # raise ResourceNotFoundException("게시글을 찾을 수 없습니다.")
            raise NotFound("게시글을 찾을 수 없습니다.")

        qs = Comment.objects.filter(post_id=post_id)
        qs = qs.annotate(like_count=Count("likes"))

        user = self.request.user

        if user and user.is_authenticated:
            liked_subquery = CommentLike.objects.filter(comment_id=OuterRef("pk"), user_id=user.id)
            qs = qs.annotate(is_liked=Exists(liked_subquery))

        else:
            qs = qs.annotate(is_liked=Value(False, output_field=BooleanField()))

        return qs.order_by("-created_at")

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        post_id: Any = self.kwargs.get("post_id")

        if not Post.objects.filter(id=post_id).exists():
            # raise ResourceNotFoundException("게시글을 찾을 수 없습니다.")
            raise NotFound("게시글을 찾을 수 없습니다.")

        serializer.save(user_id=self.request.user.id, post_id=post_id)
