from django.urls import path

from apps.posts.views.admin.admin_post_views import (
    AdminPostDeleteAPIView,
    AdminPostDetailAPIView,
    AdminPostListAPIView,
    AdminPostStatusUpdateAPIView,
)
from apps.posts.views.admin.admin_tag_views import (
    AdminTagListCreateAPIView,
    AdminTagUpdateAPIView,
)

urlpatterns = [
    path("posts", AdminPostListAPIView.as_view(), name="admin-post-list"),
    path("posts/<int:post_id>", AdminPostDetailAPIView.as_view(), name="admin-post-detail"),
    path("posts/<int:post_id>/delete", AdminPostDeleteAPIView.as_view(), name="admin-post-delete"),
    path("posts/<int:post_id>/status", AdminPostStatusUpdateAPIView.as_view(), name="admin-post-status-update"),
    path("tags", AdminTagListCreateAPIView.as_view(), name="admin-tag-list-create"),
    path("tags/<int:tag_id>", AdminTagUpdateAPIView.as_view(), name="admin-tag-update"),
]
