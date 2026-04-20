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
    total_goals_count = models.IntegerField(default=0)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname"]
    status = models.CharField(max_length=20, choices=UserStatus, default=UserStatus.ACTIVE)

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


# class Follow(models.Model):
#     follower_user_id = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         null=True,
#         related_name="팔로우하는유저id",
#         db_column="follower_id",
#         help_text="팔로우를 하는 유저",
#     )
#     following_user_id = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         related_name="팔로우받는유저id",
#         null=True,
#         db_column="following_id",
#         help_text="팔로우를 받는 유저",
#     )
#     created_at = models.DateTimeField(auto_now_add=True, help_text="생성일")

#     class Meta:
#         db_table = "follows"
#         unique_together = ("follower_user_id", "following_user_id")  # 중복 팔로우 방지
#         verbose_name = "팔로우"
#         verbose_name_plural = "팔로우 목록"
