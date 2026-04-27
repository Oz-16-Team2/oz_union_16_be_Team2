from django.urls import path

from apps.users.views import user_views

urlpatterns = [
    path("signup", user_views.SignupAPIView.as_view(), name="signup"),
    path("verification/send-email", user_views.EmailVerificationSendAPIView.as_view(), name="verification-send-email"),
    path(
        "verification/verify-email",
        user_views.EmailVerificationVerifyAPIView.as_view(),
        name="verification-verify-email",
    ),
    path("social-login/kakao/callback", user_views.KakaoSocialLoginAPIView.as_view(), name="social-login-kakao"),
    path("social-login/naver/callback", user_views.NaverSocialLoginAPIView.as_view(), name="social-login-naver"),
    path("social-login/google/callback", user_views.GoogleSocialLoginAPIView.as_view(), name="social-login-google"),
    path("login", user_views.LoginAPIView.as_view(), name="login"),
    path("logout", user_views.LogoutAPIView.as_view(), name="logout"),
    path("me/", user_views.MeAPIView.as_view(), name="me"),
    path("token/refresh", user_views.TokenRefreshAPIView.as_view(), name="token-refresh"),
    path("check-nickname", user_views.NicknameCheckAPIView.as_view(), name="check-nickname"),
    path("change-password", user_views.ChangePasswordAPIView.as_view(), name="change-password"),
]
