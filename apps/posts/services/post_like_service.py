from typing import Any

from django.db import transaction

from apps.posts.models import Post, PostLike


class PostLikeService:
    @staticmethod
    @transaction.atomic
    def toggle_like(post_id: int, user: Any) -> bool:

        post = Post.objects.get(id=post_id)
        like_queryset = PostLike.objects.filter(post=post, user=user)

        if like_queryset.exists():
            like_queryset.delete()
            return False

        PostLike.objects.create(post=post, user=user)
        return True
