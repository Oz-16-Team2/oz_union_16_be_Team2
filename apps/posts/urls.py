from django.urls import path

from apps.posts.views.Comment_views import PostCommentDetailView, PostCommentListCreateView
from apps.posts.views.like_views import CommentLikeView, PostLikeView
from apps.posts.views.post_public_views import (
    PostCollectionAPIView,
    PostDetailAPIView,
)
from apps.posts.views.post_report_views import PostReportView

urlpatterns = [
    path("", PostCollectionAPIView.as_view(), name="posts-list"),
    path("<int:post_id>/", PostDetailAPIView.as_view(), name="post-detail"),
    path("<int:post_id>/reports/", PostReportView.as_view(), name="post-report"),
    # [REQ-COMM-001] 댓글 작성, [REQ-COMM-002] 댓글 조회 API
    path("<int:post_id>/comments", PostCommentListCreateView.as_view(), name="post-comments"),
    # [REQ-COMM-003] 댓글 삭제, [REQ-COMM-006] 댓글 수정 API
    path("<int:post_id>/comments/<int:comment_id>", PostCommentDetailView.as_view(), name="post-comment-detail"),
    # [REQ-POST-007] 게시글 좋아요
    path("<int:post_id>/likes", PostLikeView.as_view(), name="post-like"),
    # [REQ-COMM-004] 댓글 좋아요
    path("comments/<int:comment_id>/likes", CommentLikeView.as_view(), name="comment-like"),
]
