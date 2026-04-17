from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from apps.core.exceptions import ConflictException, ResourceNotFoundException


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    if isinstance(exc, ConflictException):
        return Response(
            {"error_detail": exc.detail},
            status=status.HTTP_409_CONFLICT,
        )

    if isinstance(exc, ResourceNotFoundException):
        return Response(
            {"error_detail": exc.detail},
            status=status.HTTP_404_NOT_FOUND,
        )

    response = exception_handler(exc, context)

    if response is None:
        return None

    if isinstance(response.data, dict) and "detail" in response.data:
        response.data = {"error_detail": response.data["detail"]}
    else:
        response.data = {"error_detail": response.data}

    return response