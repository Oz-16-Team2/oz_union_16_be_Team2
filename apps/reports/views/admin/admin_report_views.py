from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core import DetailMessageSerializer, ErrorDetailStringSerializer, detail_response
from apps.core.admin import AdminBaseAPIView
from apps.reports.serializers.admin.admin_report_serializers import (
    AdminReportActionRequestSerializer,
    AdminReportListQuerySerializer,
    AdminReportListSuccessResponseSerializer,
)
from apps.reports.services.admin.admin_report_services import AdminReportService


class AdminReportListAPIView(AdminBaseAPIView):
    @extend_schema(
        tags=["admin-reports"],
        parameters=[
            OpenApiParameter(name="status", required=False, type=str),
            OpenApiParameter(name="target_type", required=False, type=str),
            OpenApiParameter(name="page", required=True, type=int),
            OpenApiParameter(name="size", required=True, type=int),
        ],
        responses={
            200: AdminReportListSuccessResponseSerializer,
            400: ErrorDetailStringSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        serializer = AdminReportListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        reports = AdminReportService.get_reports(
            status_value=serializer.validated_data.get("status"),
            target_type_value=serializer.validated_data.get("target_type"),
            page=serializer.validated_data["page"],
            size=serializer.validated_data["size"],
        )
        return detail_response(reports, status.HTTP_200_OK)


class AdminReportActionAPIView(AdminBaseAPIView):
    @extend_schema(
        tags=["admin-reports"],
        request=AdminReportActionRequestSerializer,
        responses={
            200: DetailMessageSerializer,
            400: ErrorDetailStringSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
            404: ErrorDetailStringSerializer,
            409: ErrorDetailStringSerializer,
        },
    )
    def post(self, request: Request, report_id: int) -> Response:
        serializer = AdminReportActionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        admin_id = request.user.id
        assert admin_id is not None

        AdminReportService.process_report(
            report_id=report_id,
            action_type=serializer.validated_data["action_type"],
            memo=serializer.validated_data.get("memo", ""),
            admin_id=admin_id,
        )
        return detail_response("신고가 처리되었습니다.", status.HTTP_200_OK)