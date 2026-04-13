from django.urls import path

from apps.posts.views.admin.admin_tag_views import (
    AdminTagListCreateAPIView,
    AdminTagUpdateAPIView,
)

urlpatterns = [
    path("tags", AdminTagListCreateAPIView.as_view(), name="admin-tag-list-create"),
    path("tags/<int:tag_id>", AdminTagUpdateAPIView.as_view(), name="admin-tag-update"),
]