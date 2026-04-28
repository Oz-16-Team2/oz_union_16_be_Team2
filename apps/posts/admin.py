from __future__ import annotations

from typing import Any, cast

from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.db.models import Count, Exists, IntegerField, OuterRef, QuerySet, Subquery
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django_stubs_ext import monkeypatch

from apps.core.choices import CommentStatus, PostStatus, TargetType
from apps.posts.models import Comment, Post, PostTag, Tag
from apps.reports.models import Report
from apps.users.constants import PROFILE_IMAGE_URL_MAP
from apps.votes.models import Vote

monkeypatch(extra_classes=[admin.ModelAdmin, admin.TabularInline])


class HasGoalFilter(SimpleListFilter):
    title = "목표 포함 여부"
    parameter_name = "has_goal"

    def lookups(
        self,
        request: HttpRequest,
        model_admin: Any,
    ) -> tuple[tuple[str, str], ...]:
        return (("true", "목표 있음"), ("false", "목표 없음"))

    def queryset(self, request: HttpRequest, queryset: QuerySet[Any]) -> QuerySet[Any]:
        if self.value() == "true":
            return queryset.filter(goal__isnull=False)
        if self.value() == "false":
            return queryset.filter(goal__isnull=True)
        return queryset


class HasVoteFilter(SimpleListFilter):
    title = "투표 포함 여부"
    parameter_name = "has_vote"

    def lookups(
        self,
        request: HttpRequest,
        model_admin: Any,
    ) -> tuple[tuple[str, str], ...]:
        return (("true", "투표 있음"), ("false", "투표 없음"))

    def queryset(self, request: HttpRequest, queryset: QuerySet[Any]) -> QuerySet[Any]:
        if self.value() == "true":
            return queryset.filter(has_vote_exists=True)
        if self.value() == "false":
            return queryset.filter(has_vote_exists=False)
        return queryset


class PostTagInline(admin.TabularInline[PostTag, Post]):
    model = PostTag
    extra = 0
    raw_id_fields = ("tag",)
    readonly_fields = ("tag",)

    def has_add_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False


class CommentInline(admin.TabularInline[Comment, Post]):
    model = Comment
    extra = 0
    fields = ("id", "user", "content", "status", "created_at", "updated_at", "deleted_at")
    readonly_fields = ("id", "user", "content", "status", "created_at", "updated_at", "deleted_at")
    raw_id_fields = ("user",)
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request: HttpRequest, obj: Post | None = None) -> bool:
        return False


@admin.register(Post)
class PostAdmin(admin.ModelAdmin[Post]):
    change_list_template = "admin/posts/post/change_list.html"
    change_form_template = "admin/posts/post/change_form.html"
    list_display = (
        "id",
        "users_id",
        "nickname",
        "profile_image_preview",
        "title",
        "status_upper",
        "has_goal",
        "has_vote",
        "tag_names",
        "like_count",
        "scrap_count",
        "report_count",
        "image_url",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    list_display_links = ("id", "title")
    list_filter = ()
    search_fields = ("id", "title", "content", "user__id", "user__email", "user__nickname")
    readonly_fields = (
        "user",
        "profile_image_preview",
        "title",
        "content",
        "images",
        "image_url",
        "is_private",
        "goal",
        "goal_title",
        "goal_start_date",
        "goal_end_date",
        "goal_progress",
        "tag_names",
        "has_vote",
        "like_count",
        "scrap_count",
        "report_count",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    raw_id_fields = ("user", "goal")
    inlines = ()
    ordering = ("-created_at",)
    actions = ("mark_active", "mark_reported", "soft_delete_posts")
    list_per_page = 10

    fieldsets = (
        ("작성자", {"fields": ("user", "profile_image_preview")}),
        ("게시글 상태 관리", {"fields": ("status",)}),
        ("집계 정보", {"fields": ("tag_names", "has_vote", "report_count", "goal", "goal_progress")}),
        ("일시", {"fields": ("created_at", "updated_at", "deleted_at")}),
    )

    def get_model_perms(self, request: HttpRequest) -> dict[str, bool]:
        self.opts.verbose_name = "게시글"
        self.opts.verbose_name_plural = "게시글"
        return super().get_model_perms(request)

    def changelist_view(
        self,
        request: HttpRequest,
        extra_context: dict[str, Any] | None = None,
    ) -> Any:
        self.post_filter_type = request.GET.get("filter_type")

        mutable_get = request.GET.copy()
        mutable_get.pop("filter_type", None)

        request.GET = cast(Any, mutable_get)
        request.META["QUERY_STRING"] = mutable_get.urlencode()

        extra_context = extra_context or {}
        extra_context["post_filter_type"] = self.post_filter_type

        return super().changelist_view(request, extra_context)

    def get_search_results(
        self,
        request: HttpRequest,
        queryset: QuerySet[Post],
        search_term: str,
    ) -> tuple[QuerySet[Post], bool]:
        filter_type = getattr(self, "post_filter_type", None)

        if search_term and filter_type == "post_id":
            return queryset.filter(id=search_term), False
        if search_term and filter_type == "user_id":
            return queryset.filter(user_id=search_term), False

        return super().get_search_results(request, queryset, search_term)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Post | None = None) -> bool:
        return False

    def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
        report_count_subquery = (
            Report.objects.filter(target_type=TargetType.POST, target_id=OuterRef("pk"))
            .values("target_id")
            .annotate(count=Count("id"))
            .values("count")
        )

        queryset = (
            super()
            .get_queryset(request)
            .select_related("user", "goal")
            .prefetch_related("post_tags__tag", "comments__user")
            .annotate(
                like_count_value=Count("likes", distinct=True),
                scrap_count_value=Count("scraps", distinct=True),
                has_vote_exists=Exists(Vote.objects.filter(post=OuterRef("pk"))),
                report_count_value=Subquery(report_count_subquery, output_field=IntegerField()),
            )
        )

        status_value = request.GET.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)

        return cast(QuerySet[Post], queryset)

    @admin.display(description="users_id")
    def users_id(self, obj: Post) -> int:
        return obj.user_id

    @admin.display(description="닉네임")
    def nickname(self, obj: Post) -> str:
        return obj.user.nickname

    @admin.display(description="프로필 이미지")
    def profile_image_preview(self, obj: Post) -> str:
        image_url = PROFILE_IMAGE_URL_MAP.get(obj.user.profile_image)
        if not image_url:
            return "-"
        return format_html(
            '<img src="{}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;" />',
            image_url,
        )

    @admin.display(description="대표 이미지 URL")
    def image_url(self, obj: Post) -> str | None:
        images = obj.images or []
        return images[0] if images else None

    @admin.display(description="상태")
    def status_upper(self, obj: Post) -> str:
        return str(obj.status).upper()

    @admin.display(description="목표 포함", boolean=True)
    def has_goal(self, obj: Post) -> bool:
        return obj.goal_id is not None

    @admin.display(description="투표 포함", boolean=True)
    def has_vote(self, obj: Post) -> bool:
        return bool(getattr(obj, "has_vote_exists", False))

    @admin.display(description="태그")
    def tag_names(self, obj: Post) -> str:
        return ", ".join(post_tag.tag.name for post_tag in obj.post_tags.all())

    @admin.display(description="좋아요 수")
    def like_count(self, obj: Post) -> int:
        return int(getattr(obj, "like_count_value", 0) or 0)

    @admin.display(description="스크랩 수")
    def scrap_count(self, obj: Post) -> int:
        return int(getattr(obj, "scrap_count_value", 0) or 0)

    @admin.display(description="신고 수")
    def report_count(self, obj: Post) -> int:
        return int(getattr(obj, "report_count_value", 0) or 0)

    @admin.action(description="선택한 게시글 활성 처리")
    def mark_active(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        deleted_count = queryset.filter(status=PostStatus.DELETED).count()
        updated_count = queryset.exclude(status=PostStatus.DELETED).update(
            status=PostStatus.ACTIVE,
            deleted_at=None,
            updated_at=timezone.now(),
        )

        if deleted_count:
            self.message_user(request, f"삭제된 게시글 {deleted_count}개는 활성 처리할 수 없습니다.", messages.WARNING)
        self.message_user(request, f"{updated_count}개 게시글을 활성 처리했습니다.", messages.SUCCESS)

    @admin.action(description="선택한 게시글 신고됨 처리")
    def mark_reported(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        deleted_count = queryset.filter(status=PostStatus.DELETED).count()
        updated_count = queryset.exclude(status=PostStatus.DELETED).update(
            status=PostStatus.REPORTED,
            updated_at=timezone.now(),
        )

        if deleted_count:
            self.message_user(
                request, f"삭제된 게시글 {deleted_count}개는 신고됨 처리할 수 없습니다.", messages.WARNING
            )
        self.message_user(request, f"{updated_count}개 게시글을 신고됨 처리했습니다.", messages.SUCCESS)

    @admin.action(description="선택한 게시글 삭제 처리")
    def soft_delete_posts(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        updated_count = queryset.exclude(status=PostStatus.DELETED).update(
            status=PostStatus.DELETED,
            deleted_at=timezone.now(),
            updated_at=timezone.now(),
        )
        self.message_user(request, f"{updated_count}개 게시글을 삭제 처리했습니다.", messages.SUCCESS)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin[Comment]):
    change_list_template = "admin/posts/comment/change_list.html"

    list_display = (
        "id",
        "post_id_display",
        "user_id_display",
        "nickname",
        "content_preview",
        "status_upper",
        "like_count",
        "report_count",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    list_display_links = ("id", "content_preview")
    list_filter = ()
    search_fields = ("=id", "content", "=post__id", "post__title", "=user__id", "user__email", "user__nickname")
    readonly_fields = (
        "post",
        "user",
        "content",
        "status",
        "like_count",
        "report_count",
        "created_at",
        "updated_at",
        "deleted_at",
    )
    raw_id_fields = ("post", "user")
    ordering = ("-created_at",)
    actions = ("mark_active", "mark_reported", "soft_delete_comments")
    list_per_page = 16

    def get_model_perms(self, request: HttpRequest) -> dict[str, bool]:
        self.opts.verbose_name = "댓글"
        self.opts.verbose_name_plural = "댓글"
        return super().get_model_perms(request)

    @admin.display(description="post_id")
    def post_id_display(self, obj: Comment) -> str:
        url = reverse("admin:posts_post_change", args=[obj.post_id])
        return format_html('<a href="{}">{}</a>', url, obj.post_id)

    @admin.display(description="user_id")
    def user_id_display(self, obj: Comment) -> int:
        return obj.user_id

    @admin.display(description="닉네임")
    def nickname(self, obj: Comment) -> str:
        return obj.user.nickname

    def changelist_view(
        self,
        request: HttpRequest,
        extra_context: dict[str, Any] | None = None,
    ) -> Any:
        self.comment_filter_type = request.GET.get("filter_type")

        mutable_get = request.GET.copy()
        mutable_get.pop("filter_type", None)

        request.GET = cast(Any, mutable_get)
        request.META["QUERY_STRING"] = mutable_get.urlencode()

        extra_context = extra_context or {}
        extra_context["comment_filter_type"] = self.comment_filter_type

        return super().changelist_view(request, extra_context)

    def get_search_results(
        self,
        request: HttpRequest,
        queryset: QuerySet[Comment],
        search_term: str,
    ) -> tuple[QuerySet[Comment], bool]:
        filter_type = getattr(self, "comment_filter_type", None)

        if search_term and filter_type == "comment_id":
            return queryset.filter(id=search_term), False
        if search_term and filter_type == "post_id":
            return queryset.filter(post_id=search_term), False
        if search_term and filter_type == "user_id":
            return queryset.filter(user_id=search_term), False

        return super().get_search_results(request, queryset, search_term)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Comment | None = None) -> bool:
        return False

    def get_queryset(self, request: HttpRequest) -> QuerySet[Comment]:
        report_count_subquery = (
            Report.objects.filter(target_type=TargetType.COMMENT, target_id=OuterRef("pk"))
            .values("target_id")
            .annotate(count=Count("id"))
            .values("count")
        )

        queryset = (
            super()
            .get_queryset(request)
            .select_related("post", "user")
            .annotate(
                like_count_value=Count("likes", distinct=True),
                report_count_value=Subquery(report_count_subquery, output_field=IntegerField()),
            )
        )

        status_value = request.GET.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)

        return cast(QuerySet[Comment], queryset)

    @admin.display(description="댓글 내용")
    def content_preview(self, obj: Comment) -> str:
        return obj.content[:50]

    @admin.display(description="상태")
    def status_upper(self, obj: Comment) -> str:
        return str(obj.status).upper()

    @admin.display(description="좋아요 수")
    def like_count(self, obj: Comment) -> int:
        return int(getattr(obj, "like_count_value", 0) or 0)

    @admin.display(description="신고 수")
    def report_count(self, obj: Comment) -> int:
        return int(getattr(obj, "report_count_value", 0) or 0)

    @admin.action(description="선택한 댓글 활성 처리")
    def mark_active(self, request: HttpRequest, queryset: QuerySet[Comment]) -> None:
        deleted_count = queryset.filter(status=CommentStatus.DELETED).count()
        updated_count = queryset.exclude(status=CommentStatus.DELETED).update(
            status=CommentStatus.ACTIVE,
            deleted_at=None,
            updated_at=timezone.now(),
        )

        if deleted_count:
            self.message_user(request, f"삭제된 댓글 {deleted_count}개는 활성 처리할 수 없습니다.", messages.WARNING)
        self.message_user(request, f"{updated_count}개 댓글을 활성 처리했습니다.", messages.SUCCESS)

    @admin.action(description="선택한 댓글 신고됨 처리")
    def mark_reported(self, request: HttpRequest, queryset: QuerySet[Comment]) -> None:
        deleted_count = queryset.filter(status=CommentStatus.DELETED).count()
        updated_count = queryset.exclude(status=CommentStatus.DELETED).update(
            status=CommentStatus.REPORTED,
            updated_at=timezone.now(),
        )

        if deleted_count:
            self.message_user(request, f"삭제된 댓글 {deleted_count}개는 신고됨 처리할 수 없습니다.", messages.WARNING)
        self.message_user(request, f"{updated_count}개 댓글을 신고됨 처리했습니다.", messages.SUCCESS)

    @admin.action(description="선택한 댓글 삭제 처리")
    def soft_delete_comments(self, request: HttpRequest, queryset: QuerySet[Comment]) -> None:
        updated_count = queryset.exclude(status=CommentStatus.DELETED).update(
            status=CommentStatus.DELETED,
            deleted_at=timezone.now(),
            updated_at=timezone.now(),
        )
        self.message_user(request, f"{updated_count}개 댓글을 삭제 처리했습니다.", messages.SUCCESS)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin[Tag]):
    change_list_template = "admin/posts/tag/change_list.html"
    list_display = ("id", "name", "is_active", "post_count", "created_at")
    list_display_links = ("id", "name")
    list_filter = ()
    search_fields = ("id", "name")
    list_editable = ("is_active",)
    readonly_fields = ("created_at", "post_count")
    ordering = ("-created_at",)
    list_per_page = 16

    def get_model_perms(self, request: HttpRequest) -> dict[str, bool]:
        self.opts.verbose_name = "태그"
        self.opts.verbose_name_plural = "태그"
        return super().get_model_perms(request)

    def changelist_view(self, request: HttpRequest, extra_context: dict[str, Any] | None = None) -> Any:
        self.tag_filter_type = request.GET.get("filter_type")
        self.active_filter = request.GET.get("active_filter")

        mutable_get = request.GET.copy()
        mutable_get.pop("filter_type", None)
        mutable_get.pop("active_filter", None)

        request.GET = cast(Any, mutable_get)
        request.META["QUERY_STRING"] = mutable_get.urlencode()

        extra_context = extra_context or {}
        extra_context["tag_filter_type"] = self.tag_filter_type
        extra_context["active_filter"] = self.active_filter

        return super().changelist_view(request, extra_context)

    def get_search_results(
        self,
        request: HttpRequest,
        queryset: QuerySet[Tag],
        search_term: str,
    ) -> tuple[QuerySet[Tag], bool]:
        filter_type = getattr(self, "tag_filter_type", None)

        if search_term and filter_type == "tag_id":
            return queryset.filter(id=search_term), False
        if search_term and filter_type == "name":
            return queryset.filter(name__icontains=search_term), False

        return super().get_search_results(request, queryset, search_term)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Tag]:
        queryset = super().get_queryset(request).annotate(post_count_value=Count("post_tags", distinct=True))

        active_filter = getattr(self, "active_filter", None)
        if active_filter == "true":
            queryset = queryset.filter(is_active=True)
        elif active_filter == "false":
            queryset = queryset.filter(is_active=False)

        return cast(QuerySet[Tag], queryset)

    @admin.display(description="사용 게시글 수")
    def post_count(self, obj: Tag) -> int:
        return int(getattr(obj, "post_count_value", 0) or 0)
