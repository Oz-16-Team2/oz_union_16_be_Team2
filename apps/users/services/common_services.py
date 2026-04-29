from __future__ import annotations

from typing import Any

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.choices import UserStatus
from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import User


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _build_user_profile(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "nickname": user.nickname,
        "profile_image_url": PROFILE_IMAGE_URL_MAP.get(user.profile_image, ""),
    }


def _build_login_payload(user: User) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
    }


def refresh_user_status(user: User) -> User:
    now = timezone.now()

    if user.status == UserStatus.SUSPENDED and user.status_expires_at and user.status_expires_at < now:
        user.status = UserStatus.ACTIVE
        user.status_expires_at = None
        user.memo = None
        user.save(update_fields=["status", "status_expires_at", "memo", "updated_at"])

    return user


def _validate_login_user(user: User) -> User:
    user = refresh_user_status(user)

    deleted_at = getattr(user, "deleted_at", None)
    if deleted_at is not None:
        raise PermissionDenied(
            {
                "detail": "탈퇴 신청한 계정입니다.",
                "expire_at": deleted_at.strftime("%Y-%m-%d"),
            }
        )
    if user.status == UserStatus.SUSPENDED:
        raise PermissionDenied("정지된 계정입니다.")

    return user


def _get_goals_manager(user: Any) -> Any | None:
    meta = getattr(user, "_meta", None)
    related_objects = getattr(meta, "related_objects", ())

    for related in related_objects:
        related_model = getattr(related, "related_model", None)
        if related_model is None:
            continue

        accessor_name = related.get_accessor_name()
        model_name = getattr(related_model, "__name__", "").lower()
        if "goal" not in accessor_name.lower() and "goal" not in model_name:
            continue

        manager = getattr(user, accessor_name, None)
        if manager is not None and hasattr(manager, "all"):
            return manager

    for accessor_name in ("goals", "goal_set", "created_goals", "user_goals"):
        manager = getattr(user, accessor_name, None)
        if manager is not None and hasattr(manager, "all"):
            return manager

    return None


def _count_completed_goals(user: Any) -> int:
    manager = _get_goals_manager(user)
    if manager is None:
        return 0

    queryset = manager.all()
    model = getattr(queryset, "model", None)
    if model is None:
        try:
            return int(queryset.count())
        except Exception:
            return 0

    field_names = {field.name for field in model._meta.get_fields() if getattr(field, "concrete", False)}

    if "completed_at" in field_names:
        return int(queryset.filter(completed_at__isnull=False).count())

    if "is_completed" in field_names:
        return int(queryset.filter(is_completed=True).count())

    if "status" in field_names:
        try:
            status_field = model._meta.get_field("status")
            completed_values: list[Any] = []

            for choice in getattr(status_field, "choices", ()):
                if isinstance(choice, (tuple, list)) and len(choice) == 2:
                    value, label = choice
                else:
                    value = choice
                    label = choice

                choice_text = f"{value} {label}".upper()
                if (
                    "COMPLETE" in choice_text
                    or "DONE" in choice_text
                    or "FINISH" in choice_text
                    or "완료" in str(label)
                ):
                    completed_values.append(value)

            if completed_values:
                return int(queryset.filter(status__in=completed_values).count())
        except Exception:
            pass

    return 0
