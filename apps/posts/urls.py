from django.urls import path

from apps.posts.views.comment_views import PostCommentDetailView, PostCommentListCreateView
from apps.posts.views.like_views import CommentLikeView
from apps.posts.views.post_public_views import (
    PostCollectionAPIView,
    PostDetailAPIView,
    PresignedUrlAPIView,
)
from apps.posts.views.post_report_views import PostReportView
from apps.posts.views.post_suggestion_views import PostSuggestionAPIView
from apps.posts.views.post_trending_views import PostTrendingAPIView
from apps.posts.views.scrap_views import PostScrapView, UserScrapListView
from apps.posts.views.tag_views import TagListView

urlpatterns = [
    path("", PostCollectionAPIView.as_view(), name="posts-list"),
    path("<int:post_id>/", PostDetailAPIView.as_view(), name="post-detail"),
    path("<int:post_id>/reports/", PostReportView.as_view(), name="post-report"),
    # [REQ-COMM-001] 댓글 작성, [REQ-COMM-002] 댓글 조회 API
    path("<int:post_id>/comments", PostCommentListCreateView.as_view(), name="post-comments"),
    # [REQ-COMM-003] 댓글 삭제, [REQ-COMM-006] 댓글 수정 API
    path("<int:post_id>/comments/<int:comment_id>", PostCommentDetailView.as_view(), name="post-comment-detail"),
    # [REQ-COMM-004] 댓글 좋아요
    path("comments/<int:comment_id>/likes", CommentLikeView.as_view(), name="comment-like"),
    path("presigned-url/", PresignedUrlAPIView.as_view(), name="presigned-url"),
    # [REQ-SCRP-001,REQ-SCRP-003]특정 게시글 스크랩(POST) / 취소(DELETE)
    path("<int:post_id>/scraps", PostScrapView.as_view(), name="post-scrap"),
    # [REQ-SCRP-002]내 스크랩 전체 목록 조회 (GET)
    path("scraps", UserScrapListView.as_view(), name="user-scrap-list"),
    # [REQ-TAG-002] 태그 조회
    path("tags", TagListView.as_view(), name="tag-list"),
    # [REQ-TAG-003] 추천 게시글 조회
    path("suggestions", PostSuggestionAPIView.as_view(), name="post-suggestions"),
    # 인기 게시글 조회 (요즘 뜨는 글 / 지금 핫한 글)
    path("trending", PostTrendingAPIView.as_view(), name="post-trending"),
]
