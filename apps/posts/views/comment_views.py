from typing import Any, cast

from django.db.models import BooleanField, Count, Exists, OuterRef, Value
from django.db.models.query import QuerySet
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from apps.posts.models import Comment, CommentLike, Post
from apps.posts.serializers.comment_serializers import (
    CommentCreateSerializer,
    CommentListSerializer,
)


@extend_schema_view(
    get=extend_schema(summary="REQ-COMM-002: 댓글 목록 조회", tags=["댓글 (Comments)"]),
    post=extend_schema(summary="REQ-COMM-001: 댓글 작성", tags=["댓글 (Comments)"]),
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
            return cast(type[BaseSerializer[Any]], CommentCreateSerializer)
        return cast(type[BaseSerializer[Any]], CommentListSerializer)

    def get_queryset(self) -> QuerySet[Comment]:
        post_id: int = self.kwargs.get("post_id")

        if not Post.objects.filter(id=post_id, deleted_at__isnull=True).exists():
            raise NotFound("게시글을 찾을 수 없습니다.")

        qs = (
            Comment.objects.filter(post_id=post_id, deleted_at__isnull=True)
            .select_related("user")
            .prefetch_related("user__social_logins")
        )
        qs = qs.annotate(like_count=Count("likes"))

        user = self.request.user

        if user and user.is_authenticated:
            liked_subquery = CommentLike.objects.filter(comment_id=OuterRef("pk"), user_id=user.id)
            qs = qs.annotate(is_liked=Exists(liked_subquery))
        else:
            qs = qs.annotate(is_liked=Value(False, output_field=BooleanField()))

        return qs.order_by("-created_at")

    def list(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data})

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        post_id: Any = self.kwargs.get("post_id")

        if not Post.objects.filter(id=post_id, deleted_at__isnull=True).exists():
            raise NotFound("게시글을 찾을 수 없습니다.")

        serializer.save(user_id=self.request.user.id, post_id=post_id)


@extend_schema_view(
    get=extend_schema(summary="댓글 상세 조회 (예비용)", tags=["댓글 (Comments)"]),
    patch=extend_schema(
        summary="REQ-COMM-006: 댓글 수정",
        description="본인이 작성한 댓글의 내용을 수정합니다.<br>작성자 본인만 호출할 수 있습니다.",
        tags=["댓글 (Comments)"],
    ),
    delete=extend_schema(
        summary="REQ-COMM-003: 댓글 삭제",
        description="본인이 작성한 댓글을 삭제합니다. (Soft Delete) <br> 작성자 본인만 호출할 수 있습니다.",
        tags=["댓글 (Comments)"],
    ),
    put=extend_schema(exclude=True),
)
class PostCommentDetailView(generics.RetrieveUpdateDestroyAPIView):  # type: ignore[type-arg]
    """
    특정 댓글의 수정(PATCH), 삭제(DELETE) 뷰 , 조회 (GET-예비용)
    URL: /api/v1/posts/{post_id}/comments/{comment_id}
    """

    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "comment_id"

    def get_serializer_class(self) -> type[BaseSerializer[Any]]:
        return cast(type[BaseSerializer[Any]], CommentCreateSerializer)

    def get_queryset(self) -> QuerySet[Comment]:
        post_id: Any = self.kwargs.get("post_id")
        return Comment.objects.filter(post_id=post_id, deleted_at__isnull=True)

    def patch(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """PATCH: 부분 수정 처리"""
        return self.partial_update(request, *args, **kwargs)

    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        """PATCH: 댓글 수정 로직 (권한 체크 포함)"""

        instance = serializer.instance
        if instance is None:
            raise NotFound("수정할 댓글이 존재하지 않습니다.")

        if instance.user_id != self.request.user.id:
            raise PermissionDenied("댓글을 수정할 권한이 없습니다.")

        serializer.save()

    def perform_destroy(self, instance: Comment) -> None:
        """DELETE: 댓글 삭제 로직 (Soft Delete 구현)"""
        if instance.user_id != self.request.user.id:
            raise PermissionDenied("댓글을 삭제할 권한이 없습니다.")

        instance.deleted_at = timezone.now()
        instance.save()

    def destroy(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """DELETE: 성공 시 204 No Content 반환"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
