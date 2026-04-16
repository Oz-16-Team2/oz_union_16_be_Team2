from django.urls import path

from apps.goals.views.goal_create import GoalCheckView, GoalCreateView, GoalDetailView

urlpatterns = [
    path("", GoalCreateView.as_view(), name="goal-create"),
    path("<int:goal_id>/", GoalDetailView.as_view(), name="goal-detail"),
    path("<int:goal_id>/check/", GoalCheckView.as_view(), name="goal-check"),
]
