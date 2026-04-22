# apps/users/services/admin/admin_user_services.py

from __future__ import annotations

from typing import Any

from django.db.models import Count

from apps.core.choices import TargetType
from apps.core.exceptions import ResourceNotFoundException
from apps.posts.models import Comment, Post
from apps.reports.models import Report
from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import User


class AdminUserService:
    @staticmethod
    def get_users(*, page: int, size: int, status_value: str | None) -> list[dict[str, Any]]:
        queryset = User.objects.order_by("-created_at")

        if status_value is not None:
            queryset = queryset.filter(status=status_value.lower())

        offset = (page - 1) * size
        users = list(queryset[offset : offset + size])

        user_ids = [user.id for user in users]

        post_rows = list(Post.objects.filter(user_id__in=user_ids).values("id", "user_id"))
        comment_rows = list(Comment.objects.filter(user_id__in=user_ids).values("id", "user_id"))

        post_count_map = {
            item["user_id"]: item["count"]
            for item in (Post.objects.filter(user_id__in=user_ids).values("user_id").annotate(count=Count("id")))
        }

        comment_count_map = {
            item["user_id"]: item["count"]
            for item in (Comment.objects.filter(user_id__in=user_ids).values("user_id").annotate(count=Count("id")))
        }

        post_user_map = {row["id"]: row["user_id"] for row in post_rows}
        comment_user_map = {row["id"]: row["user_id"] for row in comment_rows}

        post_report_count_map = {user_id: 0 for user_id in user_ids}
        comment_report_count_map = {user_id: 0 for user_id in user_ids}

        post_ids = list(post_user_map.keys())
        comment_ids = list(comment_user_map.keys())

        if post_ids:
            post_report_rows = (
                Report.objects.filter(
                    target_type=TargetType.POST,
                    target_id__in=post_ids,
                )
                .values("target_id")
                .annotate(count=Count("id"))
            )
            for row in post_report_rows:
                owner_user_id = post_user_map.get(row["target_id"])
                if owner_user_id is not None:
                    post_report_count_map[owner_user_id] += row["count"]

        if comment_ids:
            comment_report_rows = (
                Report.objects.filter(
                    target_type=TargetType.COMMENT,
                    target_id__in=comment_ids,
                )
                .values("target_id")
                .annotate(count=Count("id"))
            )
            for row in comment_report_rows:
                owner_user_id = comment_user_map.get(row["target_id"])
                if owner_user_id is not None:
                    comment_report_count_map[owner_user_id] += row["count"]

        return [
            {
                "id": user.id,
                "email": user.email,
                "nickname": user.nickname,
                "profile_image_url": PROFILE_IMAGE_URL_MAP.get(user.profile_image),
                "status": str(user.status).upper(),
                "status_expires_at": user.status_expires_at,
                "memo": user.memo,
                "total_goals_count": user.total_goals_count,
                "post_count": post_count_map.get(user.id, 0),
                "comment_count": comment_count_map.get(user.id, 0),
                "post_report_count": post_report_count_map.get(user.id, 0),
                "comment_report_count": comment_report_count_map.get(user.id, 0),
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "deleted_at": user.deleted_at,
            }
            for user in users
        ]

    @staticmethod
    def update_user_status(*,user_id: int,status_value: str,status_expires_at,memo: str | None,) -> None:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise ResourceNotFoundException("사용자를 찾을 수 없습니다.") from exc

        user.status = status_value.lower()

        if status_value == "ACTIVE":
            user.status_expires_at = None
            user.memo = None
        else:
            user.status_expires_at = status_expires_at
            user.memo = memo

        user.save(update_fields=["status", "status_expires_at", "memo", "updated_at"])
