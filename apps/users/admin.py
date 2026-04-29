from __future__ import annotations

from typing import Any, cast

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django.contrib.admin.widgets import AdminSplitDateTime
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from django.utils import timezone
from django.utils.html import format_html
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.core.choices import TargetType, UserStatus
from apps.posts.models import Comment, Post
from apps.reports.models import Report
from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.users.models import SocialLogin, User


class UserStatusActionForm(ActionForm):
    status_expires_at = forms.SplitDateTimeField(
        required=False,
        label="정지 만료일",
        widget=AdminSplitDateTime(),
    )
    memo = forms.CharField(
        required=False,
        label="메모",
        widget=forms.TextInput(attrs={"placeholder": "메모 입력"}),
    )


class SocialLoginInline(admin.TabularInline[SocialLogin, User]):
    model = SocialLogin
    extra = 0
    fields = ("provider", "provider_user_id", "linked_at", "created_at", "updated_at")
    readonly_fields = ("provider", "provider_user_id", "linked_at", "created_at", "updated_at")
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        return False


@admin.register(User)
class UserAdmin(DjangoUserAdmin[User]):
    change_list_template = "admin/users/user/change_list.html"
    model = User
    action_form = UserStatusActionForm

    list_display = (
        "id",
        "email",
        "nickname",
        "profile_image_url",
        "total_goals_count",
        "post_count",
        "comment_count",
        "post_report_count",
        "comment_report_count",
        "status_upper",
        "memo",
        "status_expires_at",
        "is_active",
        "is_staff",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    list_filter = ()
    search_fields = ("id", "email", "nickname")
    ordering = ("-created_at",)
    list_editable = ("is_active",)
    list_per_page = 10
    readonly_fields = (
        "email",
        "nickname",
        "profile_image",
        "profile_image_url",
        "total_goals_count",
        "last_login",
        "created_at",
        "updated_at",
        "deleted_at",
        "post_count",
        "comment_count",
        "post_report_count",
        "comment_report_count",
        "is_staff",
        "is_superuser",
        "groups",
        "user_permissions",
    )
    actions = ("activate_users", "suspend_users", "hard_delete_users")
    inlines = (SocialLoginInline,)

    fieldsets = (
        ("기본 정보", {"fields": ("email", "password", "nickname", "profile_image", "profile_image_url")}),
        ("상태 관리", {"fields": ("status", "status_expires_at", "memo", "is_active", "deleted_at")}),
        (
            "활동 정보",
            {
                "fields": (
                    "total_goals_count",
                    "post_count",
                    "comment_count",
                    "post_report_count",
                    "comment_report_count",
                )
            },
        ),
        ("권한", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("일시", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            "사용자 생성",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "nickname",
                    "profile_image",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                    "status",
                ),
            },
        ),
    )

    @admin.action(description="⚠️ 유저 하드 삭제")
    def hard_delete_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        if not request.user.is_superuser:
            self.message_user(request, "슈퍼유저만 유저를 완전 삭제할 수 있습니다.", messages.ERROR)
            return

        if queryset.filter(id=request.user.id).exists():
            self.message_user(request, "자기 자신은 삭제할 수 없습니다.", messages.ERROR)
            return

        count = queryset.count()
        queryset.delete()

        self.message_user(request, f"{count}명 사용자를 완전히 삭제했습니다.", messages.WARNING)

    def get_search_results(
        self,
        request: HttpRequest,
        queryset: QuerySet[User],
        search_term: str,
    ) -> tuple[QuerySet[User], bool]:
        filter_type = getattr(self, "user_filter_type", None)

        if search_term and filter_type == "user_id":
            return queryset.filter(id=search_term), False
        if search_term and filter_type == "nickname":
            return queryset.filter(nickname__icontains=search_term), False
        if search_term and filter_type == "email":
            return queryset.filter(email__icontains=search_term), False

        return super().get_search_results(request, queryset, search_term)

    def changelist_view(self, request: HttpRequest, extra_context: dict[str, Any] | None = None) -> Any:
        self.user_filter_type = request.GET.get("filter_type")
        self.user_status_filter = request.GET.get("user_status_filter")

        mutable_get = request.GET.copy()
        mutable_get.pop("filter_type", None)
        mutable_get.pop("user_status_filter", None)

        request.GET = cast(Any, mutable_get)
        request.META["QUERY_STRING"] = mutable_get.urlencode()

        extra_context = extra_context or {}
        extra_context["user_filter_type"] = self.user_filter_type
        extra_context["user_status_filter"] = self.user_status_filter

        return super().changelist_view(request, extra_context)

    def get_model_perms(self, request: HttpRequest) -> dict[str, bool]:
        self.opts.verbose_name = "유저"
        self.opts.verbose_name_plural = "유저"
        return super().get_model_perms(request)

    def has_delete_permission(self, request: HttpRequest, obj: User | None = None) -> bool:
        return False

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def get_queryset(self, request: HttpRequest) -> QuerySet[User]:
        queryset = (
            super()
            .get_queryset(request)
            .annotate(
                post_count_value=Count("posts", distinct=True),
                comment_count_value=Count("comments", distinct=True),
            )
        )

        now = timezone.now()
        expired_user_ids = list(
            queryset.filter(status=UserStatus.SUSPENDED, status_expires_at__lt=now).values_list("id", flat=True)
        )
        if expired_user_ids:
            User.objects.filter(id__in=expired_user_ids).update(
                status=UserStatus.ACTIVE,
                status_expires_at=None,
                memo=None,
                updated_at=now,
            )

        user_status_filter = getattr(self, "user_status_filter", None)
        if user_status_filter:
            queryset = queryset.filter(status=user_status_filter)

        return queryset

    @admin.display(description="프로필 이미지")
    def profile_image_url(self, obj: User) -> str:
        image_url = PROFILE_IMAGE_URL_MAP.get(obj.profile_image)

        if not image_url:
            return "-"

        return format_html(
            '<img src="{}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;" />',
            image_url,
        )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    @admin.display(description="상태")
    def status_upper(self, obj: User) -> str:
        return str(obj.status).upper()

    @admin.display(description="게시글 수")
    def post_count(self, obj: User) -> int:
        return int(getattr(obj, "post_count_value", 0) or 0)

    @admin.display(description="댓글 수")
    def comment_count(self, obj: User) -> int:
        return int(getattr(obj, "comment_count_value", 0) or 0)

    @admin.display(description="게시글 신고 수")
    def post_report_count(self, obj: User) -> int:
        post_ids = Post.objects.filter(user=obj).values_list("id", flat=True)
        return Report.objects.filter(target_type=TargetType.POST, target_id__in=post_ids).count()

    @admin.display(description="댓글 신고 수")
    def comment_report_count(self, obj: User) -> int:
        comment_ids = Comment.objects.filter(user=obj).values_list("id", flat=True)
        return Report.objects.filter(target_type=TargetType.COMMENT, target_id__in=comment_ids).count()

    @admin.action(description="정상 처리")
    def activate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        form = self.action_form(request.POST)
        action_field = cast(forms.ChoiceField, form.fields["action"])
        action_field.choices = self.get_action_choices(request)

        if not form.is_valid():
            self.message_user(request, "입력값이 올바르지 않습니다.", messages.ERROR)
            return

        memo = form.cleaned_data.get("memo", "")

        updated_count = queryset.update(
            status=UserStatus.ACTIVE,
            status_expires_at=None,
            memo=memo,
            updated_at=timezone.now(),
        )
        self.message_user(request, f"{updated_count}명 사용자를 정상 처리했습니다.", messages.SUCCESS)

    @admin.action(description="정지 처리")
    def suspend_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        form = self.action_form(request.POST)
        action_field = cast(forms.ChoiceField, form.fields["action"])
        action_field.choices = self.get_action_choices(request)

        if form.is_valid():
            memo = form.cleaned_data.get("memo", "")
            status_expires_at = form.cleaned_data.get("status_expires_at")
        else:
            memo = request.POST.get("memo", "")
            status_expires_at = None

        updated_count = queryset.update(
            status=UserStatus.SUSPENDED,
            status_expires_at=status_expires_at,
            memo=memo,
            updated_at=timezone.now(),
        )

        self.message_user(request, f"{updated_count}명 사용자를 정지 처리했습니다.", messages.SUCCESS)


for model in (Group, BlacklistedToken, OutstandingToken):
    if model in admin.site._registry:
        admin.site.unregister(model)
