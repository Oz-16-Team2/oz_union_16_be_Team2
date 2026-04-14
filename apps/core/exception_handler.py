from __future__ import annotations

from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)

    if response is None:
        return None

    if isinstance(response.data, dict) and "detail" in response.data:
        response.data = {"error_detail": response.data["detail"]}
    else:
        response.data = {"error_detail": response.data}

    return response
