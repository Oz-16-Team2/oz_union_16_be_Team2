from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import parsers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers import (
    ChangePasswordSerializer,
    EmailVerificationSendSerializer,
    EmailVerificationVerifySerializer,
    ErrorDetailFieldListSerializer,
    LoginSerializer,
    MessageResponseSerializer,
    NicknameCheckSerializer,
    SignupSerializer,
    TokenRefreshSerializer,
)
from apps.users.services import (
    change_password,
    check_nickname,
    google_social_login,
    kakao_social_login,
    login_user,
    logout_user,
    naver_social_login,
    refresh_token,
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

        result = signup_user(**serializer.validated_data)

        return Response(result, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Accounts"])
class NicknameCheckAPIView(APIView):
    serializer_class = NicknameCheckSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="닉네임 중복 확인 API",
        parameters=[
            OpenApiParameter(name="nickname", required=True, type=str),
        ],
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

        result = check_nickname(**serializer.validated_data)

        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class EmailVerificationSendAPIView(APIView):
    serializer_class = EmailVerificationSendSerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(send_email_verification_code(), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class EmailVerificationVerifyAPIView(APIView):
    serializer_class = EmailVerificationVerifySerializer
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(verify_email(), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class KakaoSocialLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        return Response(kakao_social_login(), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class NaverSocialLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        return Response(naver_social_login(), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class GoogleSocialLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        return Response(google_social_login(), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class LoginAPIView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(login_user(), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class LogoutAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        return Response(logout_user(), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class TokenRefreshAPIView(APIView):
    serializer_class = TokenRefreshSerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(refresh_token(), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class ChangePasswordAPIView(APIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    def patch(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(change_password(), status=status.HTTP_200_OK)
