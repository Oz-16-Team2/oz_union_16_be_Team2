from django.urls import path

from apps.goals.views.goal_create import GoalCreateView, GoalDetailView

urlpatterns = [
    path("", GoalCreateView.as_view(), name="goal-create"),
    path("<int:goal_id>/", GoalDetailView.as_view(), name="goal-detail"),
]
