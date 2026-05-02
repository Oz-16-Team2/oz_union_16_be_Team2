import uuid
from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from apps.core.choices import UserStatus
from apps.users.models import User


@pytest.fixture
def django_admin_client(db: object) -> Client:
    admin_user = User.objects.create_superuser(
        email=f"django_admin_{uuid.uuid4().hex}@test.com",
        password="1234",
    )
    client = Client()
    client.force_login(admin_user)
    return client


@pytest.fixture
def target_user(db: object) -> User:
    return User.objects.create_user(
        email=f"user_{uuid.uuid4().hex}@test.com",
        password="1234",
        nickname=f"user_{uuid.uuid4().hex[:8]}",
    )


@pytest.mark.django_db
class TestDjangoAdminUserViews:
    def test_user_list(self, django_admin_client: Client, target_user: User) -> None:
        response = django_admin_client.get("/admin/users/user/")

        assert response.status_code == 200
        assert "delete_selected" not in response.content.decode()

    def test_suspend_user_action(self, django_admin_client: Client, target_user: User) -> None:
        future = timezone.now() + timedelta(days=7)

        response = django_admin_client.post(
            "/admin/users/user/",
            {
                "action": "suspend_users",
                "_selected_action": [str(target_user.id)],
                "memo": "도배성 게시글 작성",
                "status_expires_at_0": future.strftime("%Y-%m-%d"),
                "status_expires_at_1": future.strftime("%H:%M:%S"),
            },
            follow=True,
        )

        target_user.refresh_from_db()

        assert response.status_code == 200
        assert target_user.status == UserStatus.SUSPENDED
        assert target_user.memo == "도배성 게시글 작성"
        assert target_user.status_expires_at is not None

    def test_activate_user_action(self, django_admin_client: Client, target_user: User) -> None:
        target_user.status = UserStatus.SUSPENDED
        target_user.status_expires_at = timezone.now() + timedelta(days=7)
        target_user.memo = "정지 사유"
        target_user.save(update_fields=["status", "status_expires_at", "memo", "updated_at"])

        response = django_admin_client.post(
            "/admin/users/user/",
            {
                "action": "activate_users",
                "_selected_action": [str(target_user.id)],
                "memo": "정상 처리",
            },
            follow=True,
        )

        target_user.refresh_from_db()

        assert response.status_code == 200
        assert target_user.status == UserStatus.ACTIVE
        assert target_user.status_expires_at is None
        assert target_user.memo == "정상 처리"

    def test_expired_suspended_user_auto_activated_on_list(
        self,
        django_admin_client: Client,
        target_user: User,
    ) -> None:
        target_user.status = UserStatus.SUSPENDED
        target_user.status_expires_at = timezone.now() - timedelta(days=1)
        target_user.memo = "기간 만료 정지"
        target_user.save(update_fields=["status", "status_expires_at", "memo", "updated_at"])

        response = django_admin_client.get("/admin/users/user/")

        target_user.refresh_from_db()

        assert response.status_code == 200
        assert target_user.status == UserStatus.ACTIVE
        assert target_user.status_expires_at is None
        assert target_user.memo is None
