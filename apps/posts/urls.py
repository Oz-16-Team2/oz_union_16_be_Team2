from django.urls import path

from apps.posts.views.Comment import PostCommentListCreateView,PostCommentDetailView
from apps.posts.views.post_public_views import (
    PostCollectionAPIView,
    PostDetailAPIView,
)
from apps.posts.views.post_report_views import PostReportView


urlpatterns = [
    path("", PostCollectionAPIView.as_view(), name="posts-list"),
    path("<int:post_id>/", PostDetailAPIView.as_view(), name="post-detail"),
    path("<int:post_id>/reports/", PostReportView.as_view(), name="post-report"),
    # <POST>댓글 작성, <GET> 댓글 조회 API
    path("<int:post_id>/comments", PostCommentListCreateView.as_view(), name="post-comments"),
    # <PATCH> 댓글 수정, <DELETE> 댓글 삭제 API
    path("<int:post_id>/comments/<int:comment_id>", PostCommentDetailView.as_view(), name="post-comment-detail"),

]
