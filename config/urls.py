from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/goals/", include("apps.goals.urls"), name="goals"),
    path("api/v1/accounts/", include("apps.users.urls")),
    path("api/v1/posts/", include("apps.posts.urls")),
    path("api/v1/votes/", include("apps.votes.urls")),
    path("api/v1/tags/", include("apps.posts.tag_urls")),
    path("api/v1/admin/", include("apps.posts.admin_urls")),
    path("api/v1/admin/", include("apps.reports.admin_urls")),
    path("api/v1/admin/", include("apps.users.admin_urls")),
]
