from django.test import override_settings
from django.urls import path
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework.views import APIView


class ExceptionHandlerTestAPIView(APIView):
    def get(self, request: Request) -> Response:
        raise PermissionDenied("전역 핸들러 테스트")


urlpatterns = [
    path("test/exception-handler", ExceptionHandlerTestAPIView.as_view()),
]


@override_settings(ROOT_URLCONF=__name__)
class ExceptionHandlerTest(APITestCase):
    def test_global_exception_handler_changes_detail_to_error_detail(self) -> None:
        response = self.client.get("/test/exception-handler")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_detail"], "전역 핸들러 테스트")