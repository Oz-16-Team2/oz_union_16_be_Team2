from datetime import timedelta
from typing import Any
from unittest.mock import Mock

import pytest
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from apps.core.choices import ProfileImageCode, UserStatus
from apps.users.services.common_services import (
    _build_login_payload,
    _build_user_profile,
    _count_completed_goals,
    _get_goals_manager,
    _normalize_email,
    _validate_login_user,
    refresh_user_status,
)


class DummyUser:
    goals: Any = None
    goal_items: Any = None

    class Meta:
        related_objects: tuple[Any, ...] = ()

    _meta = Meta()


def test_normalize_email() -> None:
    assert _normalize_email(" TEST@EXAMPLE.COM ") == "test@example.com"


@pytest.mark.django_db
def test_build_user_profile(user: Any) -> None:
    user.profile_image = ProfileImageCode.AVATAR_01

    result = _build_user_profile(user)

    assert result["id"] == user.id
    assert result["nickname"] == user.nickname
    assert "profile_image_url" in result


@pytest.mark.django_db
def test_build_login_payload(user: Any) -> None:
    result = _build_login_payload(user)

    assert "access_token" in result
    assert "refresh_token" in result


@pytest.mark.django_db
def test_refresh_user_status_changes_expired_suspended_user_to_active(user: Any) -> None:
    user.status = UserStatus.SUSPENDED
    user.status_expires_at = timezone.now() - timedelta(days=1)
    user.memo = "정지"
    user.save(update_fields=["status", "status_expires_at", "memo"])

    result = refresh_user_status(user)

    assert result.status == UserStatus.ACTIVE
    assert result.status_expires_at is None
    assert result.memo is None


@pytest.mark.django_db
def test_refresh_user_status_keeps_active_user(user: Any) -> None:
    user.status = UserStatus.ACTIVE
    user.status_expires_at = None
    user.save(update_fields=["status", "status_expires_at"])

    result = refresh_user_status(user)

    assert result.status == UserStatus.ACTIVE


@pytest.mark.django_db
def test_refresh_user_status_keeps_non_expired_suspended_user(user: Any) -> None:
    user.status = UserStatus.SUSPENDED
    user.status_expires_at = timezone.now() + timedelta(days=1)
    user.save(update_fields=["status", "status_expires_at"])

    result = refresh_user_status(user)

    assert result.status == UserStatus.SUSPENDED
    assert result.status_expires_at is not None


@pytest.mark.django_db
def test_validate_login_user_success(user: Any) -> None:
    result = _validate_login_user(user)

    assert result == user


@pytest.mark.django_db
def test_validate_login_user_rejects_deleted_user(user: Any) -> None:
    user.deleted_at = timezone.now()

    with pytest.raises(PermissionDenied):
        _validate_login_user(user)


@pytest.mark.django_db
def test_validate_login_user_rejects_suspended_user(user: Any) -> None:
    user.status = UserStatus.SUSPENDED
    user.status_expires_at = timezone.now() + timedelta(days=1)
    user.save(update_fields=["status", "status_expires_at"])

    with pytest.raises(PermissionDenied):
        _validate_login_user(user)


def test_get_goals_manager_returns_none_without_related_manager() -> None:
    user = DummyUser()

    assert _get_goals_manager(user) is None


def test_get_goals_manager_fallback_goals() -> None:
    manager = Mock()
    manager.all.return_value = []

    user = DummyUser()
    user.goals = manager

    assert _get_goals_manager(user) == manager


def test_get_goals_manager_from_related_objects() -> None:
    manager = Mock()
    manager.all.return_value = []

    related_model = Mock()
    related_model.__name__ = "Goal"

    related = Mock()
    related.related_model = related_model
    related.get_accessor_name.return_value = "goal_items"

    user = DummyUser()
    user._meta.related_objects = (related,)
    user.goal_items = manager

    assert _get_goals_manager(user) == manager


def test_count_completed_goals_without_manager_returns_zero() -> None:
    user = DummyUser()

    assert _count_completed_goals(user) == 0


def test_count_completed_goals_when_queryset_has_no_model() -> None:
    queryset = Mock()
    queryset.model = None
    queryset.count.return_value = 3

    manager = Mock()
    manager.all.return_value = queryset

    user = DummyUser()
    user.goals = manager

    assert _count_completed_goals(user) == 3


def test_count_completed_goals_when_queryset_count_raises_error() -> None:
    queryset = Mock()
    queryset.model = None
    queryset.count.side_effect = Exception

    manager = Mock()
    manager.all.return_value = queryset

    user = DummyUser()
    user.goals = manager

    assert _count_completed_goals(user) == 0


def test_count_completed_goals_by_completed_at_field() -> None:
    field = Mock()
    field.name = "completed_at"
    field.concrete = True

    model = Mock()
    model._meta.get_fields.return_value = [field]

    queryset = Mock()
    queryset.model = model
    queryset.filter.return_value.count.return_value = 2

    manager = Mock()
    manager.all.return_value = queryset

    user = DummyUser()
    user.goals = manager

    assert _count_completed_goals(user) == 2
    queryset.filter.assert_called_once_with(completed_at__isnull=False)


def test_count_completed_goals_by_is_completed_field() -> None:
    field = Mock()
    field.name = "is_completed"
    field.concrete = True

    model = Mock()
    model._meta.get_fields.return_value = [field]

    queryset = Mock()
    queryset.model = model
    queryset.filter.return_value.count.return_value = 4

    manager = Mock()
    manager.all.return_value = queryset

    user = DummyUser()
    user.goals = manager

    assert _count_completed_goals(user) == 4
    queryset.filter.assert_called_once_with(is_completed=True)


def test_count_completed_goals_by_status_field() -> None:
    status_field = Mock()
    status_field.name = "status"
    status_field.concrete = True
    status_field.choices = (
        ("TODO", "진행 전"),
        ("DONE", "완료"),
    )

    model_meta = Mock()
    model_meta.get_fields.return_value = [status_field]
    model_meta.get_field.return_value = status_field

    model = Mock()
    model._meta = model_meta

    queryset = Mock()
    queryset.model = model
    queryset.filter.return_value.count.return_value = 5

    manager = Mock()
    manager.all.return_value = queryset

    user = DummyUser()
    user.goals = manager

    assert _count_completed_goals(user) == 5
    queryset.filter.assert_called_once_with(status__in=["DONE"])


def test_count_completed_goals_returns_zero_without_completed_fields() -> None:
    field = Mock()
    field.name = "title"
    field.concrete = True

    model = Mock()
    model._meta.get_fields.return_value = [field]

    queryset = Mock()
    queryset.model = model

    manager = Mock()
    manager.all.return_value = queryset

    user = DummyUser()
    user.goals = manager

    assert _count_completed_goals(user) == 0
