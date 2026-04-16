from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import parsers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers import (
    ChangePasswordSerializer,
    EmailVerificationSendSerializer,
    EmailVerificationSuccessSerializer,
    EmailVerificationVerifySerializer,
    ErrorDetailFieldListSerializer,
    ErrorDetailStringSerializer,
    ErrorDetailWithdrawnSerializer,
    LoginSerializer,
    MessageResponseSerializer,
    NicknameCheckSerializer,
    SignupSerializer,
    TokenRefreshSerializer,
    TokenResponseSerializer,
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

        result = check_nickname(**serializer.validated_data)

        return Response(result, status=status.HTTP_200_OK)


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
        },
        examples=[
            OpenApiExample(
                "인증 메일 발송 성공",
                value={"detail": "이메일 인증 코드가 전송되었습니다."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "인증 메일 발송 실패",
                value={"error_detail": {"email": ["이 필드는 필수 항목입니다."]}},
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(send_email_verification_code(), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class EmailVerificationVerifyAPIView(APIView):
    serializer_class = EmailVerificationVerifySerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="이메일 인증 확인",
        parameters=[
            OpenApiParameter(name="email", required=True, type=str),
            OpenApiParameter(name="code", required=True, type=str),
        ],
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
    def get(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(verify_email(), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class KakaoSocialLoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="소셜 카카오 회원가입,로그인")
    def post(self, request: Request) -> Response:
        return Response(kakao_social_login(), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class NaverSocialLoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="소셜 네이버 회원가입,로그인")
    def post(self, request: Request) -> Response:
        return Response(naver_social_login(), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class GoogleSocialLoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="소셜 구글 회원가입,로그인")
    def post(self, request: Request) -> Response:
        return Response(google_social_login(), status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class LoginAPIView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="이메일 로그인",
        request=LoginSerializer,
        responses={
            200: TokenResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailWithdrawnSerializer,
        },
        examples=[
            OpenApiExample(
                "이메일 로그인 성공",
                value={"access_token": "JWT Token Value"},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "이메일 로그인 실패 - 필수값 누락",
                value={
                    "error_detail": {
                        "email": ["이 필드는 필수 항목입니다."],
                        "password": ["이 필드는 필수 항목입니다."],
                    }
                },
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "이메일 로그인 실패 - 인증 실패",
                value={"error_detail": "이메일 또는 비밀번호가 올바르지 않습니다."},
                response_only=True,
                status_codes=["401"],
            ),
            OpenApiExample(
                "이메일 로그인 실패 - 탈퇴 계정",
                value={
                    "error_detail": {
                        "detail": "탈퇴 신청한 계정입니다.",
                        "expire_at": "YYYY-MM-DD",
                    }
                },
                response_only=True,
                status_codes=["403"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = login_user(**serializer.validated_data)
        refresh_token = result.pop("refresh_token")

        response = Response(result, status=status.HTTP_200_OK)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="Lax",
        )
        return response


@extend_schema(tags=["Accounts"])
@extend_schema(tags=["Accounts"])
class LogoutAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="로그아웃 API",
        responses={200: MessageResponseSerializer},
        examples=[
            OpenApiExample(
                "로그아웃 성공",
                value={"detail": "로그아웃 되었습니다."},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            logout_user(refresh_token=refresh_token)

        response = Response(
            {"detail": "로그아웃 되었습니다."},
            status=status.HTTP_200_OK,
        )
        response.delete_cookie("refresh_token")
        return response


@extend_schema(tags=["Accounts"])
class TokenRefreshAPIView(APIView):
    serializer_class = TokenRefreshSerializer
    permission_classes = [AllowAny]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="JWT 토큰 재발급",
        request=TokenRefreshSerializer,
        responses={
            200: TokenResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            403: ErrorDetailStringSerializer,
        },
        examples=[
            OpenApiExample(
                "토큰 재발급 성공",
                value={"access_token": "JWT Token Value"},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "토큰 재발급 실패 - 필수값 누락",
                value={"error_detail": {"refresh_token": ["이 필드는 필수 항목입니다."]}},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "토큰 재발급 실패 - 세션 만료",
                value={"error_detail": {"detail": "로그인 세션이 만료되었습니다."}},
                response_only=True,
                status_codes=["403"],
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = refresh_token(**serializer.validated_data)

        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts"])
class ChangePasswordAPIView(APIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.JSONParser]

    @extend_schema(
        summary="비밀번호 변경",
        request=ChangePasswordSerializer,
        responses={
            200: MessageResponseSerializer,
            400: ErrorDetailFieldListSerializer,
            401: ErrorDetailStringSerializer,
            403: ErrorDetailStringSerializer,
        },
        examples=[
            OpenApiExample(
                "비밀번호 변경 성공",
                value={"detail": "비밀번호가 변경되었습니다."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "비밀번호 변경 실패 - 형식/검증 오류",
                value={
                    "error_detail": {
                        "new_password": ["비밀번호 형식이 올바르지 않습니다."],
                        "new_password_confirm": ["비밀번호가 일치하지 않습니다."],
                    }
                },
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "비밀번호 변경 실패 - 인증 필요",
                value={"error_detail": "로그인 인증이 필요합니다."},
                response_only=True,
                status_codes=["401"],
            ),
            OpenApiExample(
                "비밀번호 변경 실패 - 기존 비밀번호 불일치",
                value={"error_detail": "기존 비밀번호가 일치하지 않습니다."},
                response_only=True,
                status_codes=["403"],
            ),
        ],
    )
    def patch(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = change_password(
            user=request.user,
            password=serializer.validated_data["password"],
            new_password=serializer.validated_data["new_password"],
        )

        return Response(result, status=status.HTTP_200_OK)
