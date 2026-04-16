from django.urls import path

from apps.posts.views.Comment import PostCommentListCreateView
from apps.posts.views.post_public_views import (
    PostCollectionAPIView,
    PostDetailAPIView,
)

app_name = "posts"

urlpatterns = [
    path("", PostCollectionAPIView.as_view(), name="posts-list"),
    path("<int:post_id>/", PostDetailAPIView.as_view(), name="post-detail"),
    # <POST>댓글 작성, <GET> 댓글 조회 API
    path("<int:post_id>/comments", PostCommentListCreateView.as_view(), name="post-comments"),
]
