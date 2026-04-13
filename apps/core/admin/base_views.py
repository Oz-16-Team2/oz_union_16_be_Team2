from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ConflictException, ResourceNotFoundException
from apps.core.responses import error_response


class AdminBaseAPIView(APIView):  # type: ignore[misc]
    validation_error_msg = "잘못된 요청입니다."
    authentication_error_msg = "관리자 인증이 필요합니다."
    permission_error_msg = "권한이 없습니다."
    not_found_error_msg = "해당 정보를 찾을 수 없습니다."

    def handle_exception(self, exc: Exception) -> Response:
        if isinstance(exc, exceptions.ValidationError):
            return error_response(
                self.validation_error_msg,
                status.HTTP_400_BAD_REQUEST,
            )

        if isinstance(exc, (exceptions.NotAuthenticated, exceptions.AuthenticationFailed)):
            return error_response(
                self.authentication_error_msg,
                status.HTTP_401_UNAUTHORIZED,
            )

        if isinstance(exc, exceptions.PermissionDenied):
            return error_response(
                self.permission_error_msg,
                status.HTTP_403_FORBIDDEN,
            )

        if isinstance(exc, ResourceNotFoundException):
            return error_response(
                exc.detail,
                status.HTTP_404_NOT_FOUND,
            )

        if isinstance(exc, (exceptions.NotFound, Http404)):
            detail = str(exc.detail) if hasattr(exc, "detail") else self.not_found_error_msg
            return error_response(
                detail,
                status.HTTP_404_NOT_FOUND,
            )

        if isinstance(exc, ConflictException):
            return error_response(
                exc.detail,
                status.HTTP_409_CONFLICT,
            )

        return super().handle_exception(exc)
