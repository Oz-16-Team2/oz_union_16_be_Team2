from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager, PermissionsMixin
from django.db import models

from apps.core.choices import ProfileImageCode, UserStatus


class UserManager(BaseUserManager["User"]):
    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: object,
    ) -> User:
        if not email:
            raise ValueError("이메일은 필수입니다.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: object,
    ) -> User:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    nickname = models.CharField(max_length=100, unique=True)
    profile_image = models.CharField(max_length=20, choices=ProfileImageCode, default=ProfileImageCode.AVATAR_01)
    social_profile_image_url = models.URLField(max_length=1000, null=True, blank=True)
    total_goals_count = models.IntegerField(default=0)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname"]
    status = models.CharField(max_length=20, choices=UserStatus, default=UserStatus.ACTIVE)
    status_expires_at = models.DateTimeField(null=True, blank=True)
    # 정지(SUSPENDED) 또는 제한(RESTRICTED) 상태가 해제되는 시점 (기한 없으면 null)
    memo = models.TextField(null=True, blank=True)
    # 관리자 메모 (정지/제한 사유 등 기록)

    objects = UserManager()

    class Meta:
        db_table = "users"

    def __str__(self) -> str:
        return f"{self.email} ({self.nickname})"


class SocialLogin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="social_logins")
    provider = models.CharField(max_length=50)
    provider_user_id = models.CharField(max_length=255)
    linked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "social_login"
        unique_together = ("provider", "provider_user_id")

    def __str__(self) -> str:
        return f"{self.user.email} - {self.provider}"
