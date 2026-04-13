from __future__ import annotations

from rest_framework.response import Response


def detail_response(data: object, status_code: int) -> Response:
    return Response({"detail": data}, status=status_code)


def error_response(data: object, status_code: int) -> Response:
    return Response({"error_detail": data}, status=status_code)
