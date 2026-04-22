from __future__ import annotations

from datetime import datetime
from typing import Any

from django.db.models import Count
from django.utils import timezone

from apps.core.choices import TargetType, UserStatus
from apps.core.exceptions import ResourceNotFoundException
from apps.posts.models import Comment, Post
from apps.reports.models import Report
from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import User


class AdminUserService:
    @staticmethod
    def get_users(
        *,
        page: int,
        size: int,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        queryset = User.objects.order_by("-created_at")

        if status:
            queryset = queryset.filter(status=status.lower())

        offset = (page - 1) * size
        users = list(queryset[offset : offset + size])

        now = timezone.now()
        for user in users:
            if user.status == UserStatus.SUSPENDED:
                if user.status_expires_at and user.status_expires_at < now:
                    user.status = UserStatus.ACTIVE
                    user.status_expires_at = None
                    user.memo = None
                    user.save(
                        update_fields=[
                            "status",
                            "status_expires_at",
                            "memo",
                            "updated_at",
                        ]
                    )

        user_ids = [user.id for user in users]

        post_count_map = {
            item["user_id"]: item["count"]
            for item in (
                Post.objects.filter(user_id__in=user_ids)
                .values("user_id")
                .annotate(count=Count("id"))
            )
        }

        comment_count_map = {
            item["user_id"]: item["count"]
            for item in (
                Comment.objects.filter(user_id__in=user_ids)
                .values("user_id")
                .annotate(count=Count("id"))
            )
        }

        post_rows = list(Post.objects.filter(user_id__in=user_ids).values("id", "user_id"))
        comment_rows = list(Comment.objects.filter(user_id__in=user_ids).values("id", "user_id"))

        post_user_map = {row["id"]: row["user_id"] for row in post_rows}
        comment_user_map = {row["id"]: row["user_id"] for row in comment_rows}

        post_report_count_map = {user_id: 0 for user_id in user_ids}
        comment_report_count_map = {user_id: 0 for user_id in user_ids}

        if post_user_map:
            for row in (
                Report.objects.filter(
                    target_type=TargetType.POST,
                    target_id__in=post_user_map.keys(),
                )
                .values("target_id")
                .annotate(count=Count("id"))
            ):
                owner = post_user_map.get(row["target_id"])
                if owner is not None:
                    post_report_count_map[owner] += row["count"]

        if comment_user_map:
            for row in (
                Report.objects.filter(
                    target_type=TargetType.COMMENT,
                    target_id__in=comment_user_map.keys(),
                )
                .values("target_id")
                .annotate(count=Count("id"))
            ):
                owner = comment_user_map.get(row["target_id"])
                if owner is not None:
                    comment_report_count_map[owner] += row["count"]

        return [
            {
                "id": user.id,
                "email": user.email,
                "nickname": user.nickname,
                "profile_image_url": PROFILE_IMAGE_URL_MAP.get(user.profile_image),
                "total_goals_count": user.total_goals_count,
                "post_count": post_count_map.get(user.id, 0),
                "comment_count": comment_count_map.get(user.id, 0),
                "post_report_count": post_report_count_map.get(user.id, 0),
                "comment_report_count": comment_report_count_map.get(user.id, 0),
                "status": str(user.status).upper(),
                "memo": user.memo,
                "status_expires_at": user.status_expires_at,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "deleted_at": user.deleted_at,
            }
            for user in users
        ]

    @staticmethod
    def update_user_status(
        *,
        user_id: int,
        status_value: str,
        status_expires_at: datetime | None,
        memo: str | None,
    ) -> None:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise ResourceNotFoundException("사용자를 찾을 수 없습니다.") from exc

        normalized_status = status_value.lower()
        user.status = normalized_status

        if normalized_status == UserStatus.ACTIVE:
            user.status_expires_at = None
            user.memo = None
        else:
            user.status_expires_at = status_expires_at
            user.memo = memo

        user.save(
            update_fields=[
                "status",
                "status_expires_at",
                "memo",
                "updated_at",
            ]
        )