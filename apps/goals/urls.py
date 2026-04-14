from django.urls import path

from apps.goals.views.goal_create import GoalDetailView, GoalListCreateView

urlpatterns = [
    path("", GoalListCreateView.as_view(), name="goal-create"),
    path("<int:goal_id>/", GoalDetailView.as_view(), name="goal-detail"),
]
