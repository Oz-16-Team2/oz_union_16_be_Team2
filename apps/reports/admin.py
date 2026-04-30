from __future__ import annotations

from typing import Any, cast

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeString

from apps.core.choices import TargetType
from apps.core.exceptions import ConflictException, ResourceNotFoundException
from apps.posts.models import Comment, Post
from apps.reports.models import Report, ReportAction
from apps.reports.services.admin.admin_report_services import AdminReportService


class ReportActionMemoForm(ActionForm):
    memo = forms.CharField(
        required=False,
        label="메모",
        widget=forms.TextInput(attrs={"placeholder": "처리 메모 입력"}),
    )


class ReportActionInline(admin.TabularInline[ReportAction, Report]):
    model = ReportAction
    extra = 0
    fields = ("admin", "action_type", "memo", "created_at")
    readonly_fields = ("admin", "action_type", "memo", "created_at")
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj: Report | None = None) -> bool:
        return False


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin[Report]):
    change_list_template = "admin/reports/report/change_list.html"
    list_filter = ()
    action_form = ReportActionMemoForm

    list_display = (
        "id",
        "user_id",
        "admin_id",
        "target_type_upper",
        "target_display_id",
        "target_preview",
        "reason_type_upper",
        "reason_detail",
        "status_upper",
        "latest_action_type",
        "latest_action_memo",
        "handled_at",
        "created_at",
        "updated_at",
    )
    list_per_page = 16
    search_fields = ("id", "user__email", "user__nickname", "admin__email", "admin__nickname", "reason_detail")
    readonly_fields = (
        "user",
        "admin",
        "status",
        "target_type",
        "target_display_id",
        "target_preview",
        "reason_type",
        "reason_detail",
        "latest_action_type",
        "latest_action_memo",
        "handled_at",
        "created_at",
        "updated_at",
    )
    raw_id_fields = ("user", "admin")
    inlines = (ReportActionInline,)
    ordering = ("-created_at",)
    actions = ("delete_target_and_handle", "keep_target_and_dismiss")

    def changelist_view(
        self,
        request: HttpRequest,
        extra_context: dict[str, Any] | None = None,
    ) -> Any:
        self.status_filter = request.GET.get("status_filter")
        self.target_type_filter = request.GET.get("target_type_filter")

        mutable_get = request.GET.copy()
        mutable_get.pop("status_filter", None)
        mutable_get.pop("target_type_filter", None)

        request.GET = cast(Any, mutable_get)
        request.META["QUERY_STRING"] = mutable_get.urlencode()

        extra_context = extra_context or {}
        extra_context["status_filter"] = self.status_filter
        extra_context["target_type_filter"] = self.target_type_filter

        return super().changelist_view(request, extra_context)

    def get_model_perms(self, request: HttpRequest) -> dict[str, bool]:
        self.opts.verbose_name = "신고"
        self.opts.verbose_name_plural = "신고"
        return super().get_model_perms(request)

    @admin.display(description="대상 ID")
    def target_display_id(self, obj: Report) -> str:
        if obj.target_type == TargetType.POST:
            return f"게시글 ID: {obj.target_id}"
        if obj.target_type == TargetType.COMMENT:
            return f"댓글 ID: {obj.target_id}"
        return str(obj.target_id)

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def get_queryset(self, request: HttpRequest) -> QuerySet[Report]:
        queryset = super().get_queryset(request).select_related("user", "admin").prefetch_related("신고ID")

        status_filter = getattr(self, "status_filter", None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        target_type_filter = getattr(self, "target_type_filter", None)
        if target_type_filter:
            queryset = queryset.filter(target_type=target_type_filter)

        return queryset

    @admin.display(description="user_id")
    def user_id(self, obj: Report) -> int:
        return obj.user_id

    @admin.display(description="admin_id")
    def admin_id(self, obj: Report) -> int | None:
        return obj.admin_id

    @admin.display(description="대상 타입")
    def target_type_upper(self, obj: Report) -> str:
        return str(obj.target_type).upper()

    @admin.display(description="신고 사유")
    def reason_type_upper(self, obj: Report) -> str:
        return str(obj.reason_type).upper()

    @admin.display(description="상태")
    def status_upper(self, obj: Report) -> str:
        return str(obj.status).upper()

    @admin.display(description="신고 대상")
    def target_preview(self, obj: Report) -> str | SafeString:
        if obj.target_type == TargetType.POST:
            post = Post.objects.filter(id=obj.target_id).only("id", "title", "status").first()
            if post is None:
                return f"게시글 #{obj.target_id} - 삭제되었거나 존재하지 않음"

            url = reverse("admin:posts_post_change", args=[post.id])
            return format_html(
                '<a href="{}">게시글 #{} / {} / {}</a>',
                url,
                post.id,
                post.title,
                str(post.status).upper(),
            )

        comment = Comment.objects.filter(id=obj.target_id).only("id", "content", "status").first()
        if comment is None:
            return f"댓글 #{obj.target_id} - 삭제되었거나 존재하지 않음"

        url = reverse("admin:posts_comment_change", args=[comment.id])
        return format_html(
            '<a href="{}">댓글 #{} / {} / {}</a>',
            url,
            comment.id,
            comment.content[:30],
            str(comment.status).upper(),
        )

    def _latest_action(self, obj: Report) -> ReportAction | None:
        prefetched_actions = getattr(obj, "_prefetched_objects_cache", {}).get("신고ID")
        if prefetched_actions is not None:
            actions = sorted(prefetched_actions, key=lambda action: action.created_at, reverse=True)
            return actions[0] if actions else None

        return ReportAction.objects.filter(report=obj).order_by("-created_at").first()

    @admin.display(description="최근 처리 타입")
    def latest_action_type(self, obj: Report) -> str | None:
        latest_action = self._latest_action(obj)
        return str(latest_action.action_type).upper() if latest_action else None

    @admin.display(description="최근 처리 메모")
    def latest_action_memo(self, obj: Report) -> str | None:
        latest_action = self._latest_action(obj)
        return latest_action.memo if latest_action else None

    def _log_report_action(self, request: HttpRequest, report: Report, message: str) -> None:
        content_type = ContentType.objects.get_for_model(Report)

        LogEntry.objects.create(
            user_id=request.user.id,
            content_type_id=content_type.id,
            object_id=str(report.id),
            object_repr=str(report),
            action_flag=CHANGE,
            change_message=message,
        )

    @admin.action(description="삭제 처리")
    def delete_target_and_handle(self, request: HttpRequest, queryset: QuerySet[Report]) -> None:
        admin_id = request.user.id
        if admin_id is None:
            messages.error(request, "관리자 정보를 찾을 수 없습니다.")
            return

        memo = request.POST.get("memo", "")
        handled_count = 0

        for report in queryset:
            try:
                AdminReportService.process_report(
                    report_id=report.id,
                    action_type="DELETE",
                    memo=memo,
                    admin_id=admin_id,
                )
                handled_count += 1

                report.refresh_from_db()
                self._log_report_action(request, report, "신고 삭제 처리")
            except (ConflictException, ResourceNotFoundException) as exc:
                messages.error(request, f"신고 {report.id}번: {exc}")

        messages.success(request, f"{handled_count}개 신고를 삭제 처리했습니다.")

    @admin.action(description="유지 처리")
    def keep_target_and_dismiss(self, request: HttpRequest, queryset: QuerySet[Report]) -> None:
        admin_id = request.user.id
        if admin_id is None:
            messages.error(request, "관리자 정보를 찾을 수 없습니다.")
            return

        memo = request.POST.get("memo", "")
        handled_count = 0

        for report in queryset:
            try:
                AdminReportService.process_report(
                    report_id=report.id,
                    action_type="KEEP",
                    memo=memo,
                    admin_id=admin_id,
                )
                handled_count += 1

                report.refresh_from_db()
                self._log_report_action(request, report, "신고 유지 처리")
            except (ConflictException, ResourceNotFoundException) as exc:
                messages.error(request, f"신고 {report.id}번: {exc}")

        messages.success(request, f"{handled_count}개 신고를 유지 처리했습니다.")
