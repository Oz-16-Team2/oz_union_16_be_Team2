from typing import Any

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import parsers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ConflictException
from apps.users.serializers.account_serializers import (
    EmailVerificationSendSerializer,
    EmailVerificationVerifySerializer,
    NicknameCheckSerializer,
    SignupSerializer,
)
from apps.users.serializers.common_serializers import (
    EmailVerificationSuccessSerializer,
    ErrorDetailFieldListSerializer,
    MessageResponseSerializer,
)
from apps.users.services.account_services import (
    check_nickname,
    send_email_verification_code,
    signup_user,
    verify_email,
)


@extend_schema(tags=["Accounts"])
class SignupAPIView(APIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="이메일 회원가입",
        request=SignupSerializer,
        responses={
            201: MessageResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            409: ErrorDetailFieldListSerializer,
        },
        examples=[
            OpenApiExample(
                "회원가입 성공",
                value={"detail": "회원가입이 완료되었습니다."},
                response_only=True,
                status_codes=["201"],
            ),
            OpenApiExample(
                "회원가입 실패 - 형식 오류",
                value={
                    "error_detail": {
                        "email": ["이메일 형식이 올바르지 않습니다."],
                        "password": ["비밀번호는 8자 이상이어야 합니다."],
                    }
                },
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "회원가입 실패 - 중복",
                value={
                    "error_detail": {
                        "email": ["이미 가입된 이메일입니다."],
                        "nickname": ["이미 사용 중인 닉네임입니다."],
                    }
                },
                response_only=True,
                status_codes=["409"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = signup_user(**serializer.validated_data)
        except ConflictException as exc:
            return Response({"error_detail": exc.detail}, status=status.HTTP_409_CONFLICT)

        return Response(result, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Accounts"])
class EmailVerificationSendAPIView(APIView):
    serializer_class = EmailVerificationSendSerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="이메일 인증 발송 API",
        request=EmailVerificationSendSerializer,
        responses={
            200: MessageResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            409: ErrorDetailFieldListSerializer,
        },
        examples=[
            OpenApiExample(
                "인증 메일 발송 성공",
                value={"detail": "이메일 인증 코드가 전송되었습니다."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "인증 메일 발송 실패 - 중복",
                value={"error_detail": {"email": ["이미 가입된 이메일입니다."]}},
                response_only=True,
                status_codes=["409"],
            ),
            OpenApiExample(
                "인증 메일 발송 실패 - 필수값 누락",
                value={"error_detail": {"email": ["이 필드는 필수 항목입니다."]}},
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = send_email_verification_code(**serializer.validated_data)
        except ConflictException as exc:
            return Response({"error_detail": exc.detail}, status=status.HTTP_409_CONFLICT)

        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class EmailVerificationVerifyAPIView(APIView):
    serializer_class = EmailVerificationVerifySerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="이메일 인증 확인",
        request=EmailVerificationVerifySerializer,
        responses={
            200: EmailVerificationSuccessSerializer,
            400: ErrorDetailFieldListSerializer,
        },
        examples=[
            OpenApiExample(
                "이메일 인증 성공",
                value={
                    "detail": "이메일 인증에 성공하였습니다.",
                    "email_token": "daechungbase32",
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "이메일 인증 실패",
                value={"error_detail": {"email": ["이 필드는 필수 항목입니다."]}},
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = verify_email(
            email=serializer.validated_data["email"],
            code=serializer.validated_data["code"],
        )
        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class NicknameCheckAPIView(APIView):
    serializer_class = NicknameCheckSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="닉네임 중복 확인 API",
        parameters=[OpenApiParameter(name="nickname", required=True, type=str)],
        responses={
            200: MessageResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            409: ErrorDetailFieldListSerializer,
        },
        examples=[
            OpenApiExample(
                "닉네임 사용 가능",
                value={"detail": "사용가능한 닉네임입니다."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "닉네임 실패 - 필수값 누락",
                value={"error_detail": {"nickname": ["이 필드는 필수 항목입니다."]}},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "닉네임 실패 - 중복",
                value={"error_detail": {"nickname": ["이미 사용 중인 닉네임입니다."]}},
                response_only=True,
                status_codes=["409"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            result = check_nickname(**serializer.validated_data)
        except ConflictException as exc:
            return Response({"error_detail": exc.detail}, status=status.HTTP_409_CONFLICT)

        return Response(result, status=status.HTTP_200_OK)
