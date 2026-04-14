from typing import Any

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.goals.models import Goal
from apps.goals.serializers.goal_create import GoalSerializer
from apps.goals.services.goal_create import GoalCreateService


class GoalListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = GoalSerializer(data=request.data)
        if serializer.is_valid():
            return Response(GoalSerializer(Goal).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoalDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, goal_id: int, *args: Any, **kwargs: Any) -> Response:
        goal = get_object_or_404(Goal, id=goal_id, user=request.user)
        serializer = GoalSerializer(goal)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request: Request, goal_id: int) -> Response:
        goal = get_object_or_404(Goal, id=goal_id, user=request.user)
        serializer = GoalSerializer(goal, data=request.data, partial=True)

        if serializer.is_valid():
            try:
                updated_goal = GoalCreateService.update_goal(goal, **serializer.validated_data)
                return Response(GoalSerializer(updated_goal).data)
            except PermissionError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request: Request, goal_id: int, *args: Any, **kwargs: Any) -> Response:
        goal = get_object_or_404(Goal, id=goal_id, user=request.user)
        goal.delete()
        return Response({"detail": "목표가 삭제되었습니다."}, status=status.HTTP_200_OK)
