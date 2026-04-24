from django.urls import path

from apps.goals.views.achievement import AchievementView
from apps.goals.views.goal_create import GoalCheckView, GoalCreateView, GoalDetailView
from apps.goals.views.ranking import MonthlyRankingView, TotalRankingView, WeeklyRankingView

urlpatterns = [
    path("", GoalCreateView.as_view(), name="goal-create"),
    path("<int:goal_id>/", GoalDetailView.as_view(), name="goal-detail"),
    path("<int:goal_id>/check/", GoalCheckView.as_view(), name="goal-check"),
    path("ranking/weekly", WeeklyRankingView.as_view(), name="weekly-ranking"),
    path("ranking/monthly", MonthlyRankingView.as_view(), name="monthly-ranking"),
    path("ranking/total", TotalRankingView.as_view(), name="total-ranking"),
    path("achievement/", AchievementView.as_view(), name="achievement"),
]
