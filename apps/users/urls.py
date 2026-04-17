from django.urls import path

from apps.users import views

urlpatterns = [
    path("signup", views.SignupAPIView.as_view(), name="signup"),
    path("verification/send-email", views.EmailVerificationSendAPIView.as_view(), name="verification-send-email"),
    path("verification/verify-email", views.EmailVerificationVerifyAPIView.as_view(), name="verification-verify-email"),
    path("social-login/kakao/callback", views.KakaoSocialLoginAPIView.as_view(), name="social-login-kakao"),
    path("social-login/naver/callback", views.NaverSocialLoginAPIView.as_view(), name="social-login-naver"),
    path("social-login/google/callback", views.GoogleSocialLoginAPIView.as_view(), name="social-login-google"),
    path("login", views.LoginAPIView.as_view(), name="login"),
    path("logout", views.LogoutAPIView.as_view(), name="logout"),
    path("token/refresh", views.TokenRefreshAPIView.as_view(), name="token-refresh"),
    path("check-nickname", views.NicknameCheckAPIView.as_view(), name="check-nickname"),
    path("change-password", views.ChangePasswordAPIView.as_view(), name="change-password"),
]
