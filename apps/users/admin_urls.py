# apps/users/admin_urls.py

from django.urls import path

from apps.users.views.admin.admin_user_views import (
    AdminUserListAPIView,
    AdminUserStatusUpdateAPIView,
)

urlpatterns = [
    path("accounts", AdminUserListAPIView.as_view(), name="admin-user-list"),
    path("accounts/<int:user_id>", AdminUserStatusUpdateAPIView.as_view(), name="admin-user-status-update"),
]
