from django.urls import path

from apps.posts.views.post_public_views import (
    PostCollectionAPIView,
    PostDetailAPIView,
)

urlpatterns = [
    path("", PostCollectionAPIView.as_view(), name="posts-list"),
    path("<int:post_id>/", PostDetailAPIView.as_view(), name="post-detail"),
]
