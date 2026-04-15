from __future__ import annotations

from typing import Any

from django.db.models import Count, Exists, OuterRef
from django.utils import timezone

from apps.core.exceptions import ResourceNotFoundException
from apps.posts.models import Post
from apps.reports.models import Report
from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.votes.models import Vote


class AdminPostService:
    @staticmethod
    def get_posts(
        *,
        user_id: int | None,
        status_value: str | None,
        has_goal: bool | None,
        has_vote: bool | None,
        page: int,
        size: int,
    ) -> list[dict[str, Any]]:
        queryset = (
            Post.objects.select_related("user")
            .prefetch_related("post_tags__tag")
            .annotate(
                like_count=Count("likes", distinct=True),
                scrap_count=Count("scraps", distinct=True),
                has_vote_exists=Exists(Vote.objects.filter(post=OuterRef("pk"))),
            )
            .order_by("-created_at")
        )

        if user_id is not None:
            queryset = queryset.filter(user_id=user_id)

        if status_value is not None:
            queryset = queryset.filter(status=status_value.lower())

        if has_goal is not None:
            queryset = queryset.filter(goal__isnull=not has_goal)

        if has_vote is not None:
            queryset = queryset.filter(has_vote_exists=has_vote)

        offset = (page - 1) * size
        posts = list(queryset[offset : offset + size])

        post_ids = [post.id for post in posts]
        report_count_map = {
            item["target_id"]: item["count"]
            for item in (
                Report.objects.filter(target_type="post", target_id__in=post_ids)
                .values("target_id")
                .annotate(count=Count("id"))
            )
        }

        return [
            {
                "id": post.id,
                "users_id": post.user_id,
                "nickname": post.user.nickname,
                "profile_image_url": PROFILE_IMAGE_URL_MAP.get(post.user.profile_image),
                "title": post.title,
                "content": post.content,
                "image_url": post.images[0] if post.images else None,
                "status": str(post.status).upper(),
                "has_goal": post.goal_id is not None,
                "has_vote": post.has_vote_exists,
                "tags": [
                    {
                        "id": post_tag.tag.id,
                        "name": post_tag.tag.name,
                    }
                    for post_tag in post.post_tags.all()
                ],
                "like_count": post.like_count,
                "scrap_count": post.scrap_count,
                "report_count": report_count_map.get(post.id, 0),
                "is_private": post.is_private,
                "created_at": post.created_at,
                "updated_at": post.updated_at,
                "deleted_at": post.deleted_at,
            }
            for post in posts
        ]

    @staticmethod
    def get_post_detail(*, post_id: int) -> dict[str, Any]:
        try:
            post = (
                Post.objects.select_related("user")
                .prefetch_related(
                    "post_tags__tag",
                    "comments__user",
                    "vote__options",
                    "likes",
                    "scraps",
                )
                .annotate(
                    like_count=Count("likes", distinct=True),
                    scrap_count=Count("scraps", distinct=True),
                )
                .get(id=post_id)
            )
        except Post.DoesNotExist as exc:
            raise ResourceNotFoundException("게시글을 찾을 수 없습니다.") from exc

        vote_data: dict[str, Any] | None = None
        if hasattr(post, "vote"):
            vote = post.vote
            vote_data = {
                "id": vote.id,
                "question": vote.question,
                "start_at": vote.start_at,
                "end_at": vote.end_at,
                "status": str(vote.status),
                "options": [
                    {
                        "id": option.id,
                        "content": option.content,
                        "sort_order": option.sort_order,
                    }
                    for option in vote.options.all()
                ],
            }

        return {
            "id": post.id,
            "users_id": post.user_id,
            "nickname": post.user.nickname,
            "profile_image_url": PROFILE_IMAGE_URL_MAP.get(post.user.profile_image),
            "goals_id": post.goal_id,
            "title": post.title,
            "content": post.content,
            "status": str(post.status).upper(),
            "is_private": post.is_private,
            "images": post.images,
            "tags": [
                {
                    "id": post_tag.tag.id,
                    "name": post_tag.tag.name,
                }
                for post_tag in post.post_tags.all()
            ],
            "goal_start_date": post.goal_start_date,
            "goal_end_date": post.goal_end_date,
            "goal_title": post.goal_title,
            "goal_progress": post.goal_progress,
            "like_count": post.like_count,
            "scrap_count": post.scrap_count,
            "comments": [
                {
                    "id": comment.id,
                    "user_id": comment.user_id,
                    "nickname": comment.user.nickname,
                    "content": comment.content,
                    "status": str(comment.status).upper(),
                    "created_at": comment.created_at,
                    "updated_at": comment.updated_at,
                }
                for comment in post.comments.all().order_by("created_at")
            ],
            "vote": vote_data,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "deleted_at": post.deleted_at,
        }

    @staticmethod
    def delete_post(*, post_id: int) -> None:
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist as exc:
            raise ResourceNotFoundException("게시글을 찾을 수 없습니다.") from exc

        post.deleted_at = timezone.now()
        post.save(update_fields=["deleted_at", "updated_at"])

    @staticmethod
    def update_post_status(*, post_id: int, status_value: str) -> None:
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist as exc:
            raise ResourceNotFoundException("게시글을 찾을 수 없습니다.") from exc

        post.status = status_value.lower()
        post.save(update_fields=["status", "updated_at"])
