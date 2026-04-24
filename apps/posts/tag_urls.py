from django.urls import path

from apps.posts.views.tag_post_views import TagPostListView

urlpatterns = [
    # [REQ-POST-011] 해당 태그가 쓰인 게시글 조회
    path("<int:tag_id>/posts", TagPostListView.as_view(), name="tag-post-list"),
]
