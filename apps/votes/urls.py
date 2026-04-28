from django.urls import path

from apps.votes.views import VoteDetailAPIView, VoteParticipateAPIView

urlpatterns = [
    path("<int:vote_id>/participations/", VoteParticipateAPIView.as_view(), name="vote_participate"),
    path("<int:vote_id>/", VoteDetailAPIView.as_view(), name="vote_detail"),
]
