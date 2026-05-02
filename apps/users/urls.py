from django.urls import path

from apps.users.views.account_views import (
    EmailVerificationSendAPIView,
    EmailVerificationVerifyAPIView,
    NicknameCheckAPIView,
    SignupAPIView,
)
from apps.users.views.auth_views import LoginAPIView, LogoutAPIView, TokenRefreshAPIView
from apps.users.views.profile_views import (
    ChangePasswordAPIView,
    MeActivitySummaryAchievementRateAPIView,
    MeActivitySummaryCompletedGoalsAPIView,
    MeActivitySummaryDaysAPIView,
    MeAPIView,
    ProfileImageListAPIView,
)
from apps.users.views.social_views import GoogleSocialLoginAPIView, KakaoSocialLoginAPIView, NaverSocialLoginAPIView

urlpatterns = [
    path("signup", SignupAPIView.as_view(), name="signup"),
    path("check-nickname", NicknameCheckAPIView.as_view(), name="check-nickname"),
    path("verification/send-email", EmailVerificationSendAPIView.as_view(), name="verification-send-email"),
    path(
        "verification/verify-email",
        EmailVerificationVerifyAPIView.as_view(),
        name="verification-verify-email",
    ),
    path("social-login/kakao/callback/", KakaoSocialLoginAPIView.as_view(), name="social-login-kakao"),
    path("social-login/naver/callback/", NaverSocialLoginAPIView.as_view(), name="social-login-naver"),
    path("social-login/google/callback/", GoogleSocialLoginAPIView.as_view(), name="social-login-google"),
    path("login", LoginAPIView.as_view(), name="login"),
    path("logout", LogoutAPIView.as_view(), name="logout"),
    path("me/", MeAPIView.as_view(), name="me"),
    path(
        "me/activity-summary/days/",
        MeActivitySummaryDaysAPIView.as_view(),
        name="me-activity-summary-days",
    ),
    path(
        "me/activity-summary/achievement-rate/",
        MeActivitySummaryAchievementRateAPIView.as_view(),
        name="me-activity-summary-achievement-rate",
    ),
    path(
        "me/activity-summary/completed-goals/",
        MeActivitySummaryCompletedGoalsAPIView.as_view(),
        name="me-activity-summary-completed-goals",
    ),
    path("token/refresh", TokenRefreshAPIView.as_view(), name="token-refresh"),
    path("change-password", ChangePasswordAPIView.as_view(), name="change-password"),
    path("profile-images", ProfileImageListAPIView.as_view(), name="profile-list"),
]
