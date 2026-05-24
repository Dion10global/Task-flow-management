from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from .models import Task, TaskComment, TaskActivity
from .serializers import TaskSerializer, TaskCommentSerializer, TaskActivitySerializer, TaskStatusUpdateSerializer
from apps.projects.models import Project
from apps.accounts.permissions import IsOwnerOrAdmin


def _get_accessible_project(user, project_id):
    """Return project if user is admin or member, else raise 404."""
    try:
        if user.is_admin:
            return Project.objects.get(pk=project_id)
        return Project.objects.get(
            Q(pk=project_id) & (Q(owner=user) | Q(members=user))
        )
    except Project.DoesNotExist:
        return None


class TaskListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/v1/projects/<project_id>/tasks/"""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "priority", "assigned_to"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "due_date", "priority", "status"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Task.objects.none()
        user = self.request.user
        project_id = self.kwargs["project_id"]
        project = _get_accessible_project(user, project_id)
        if not project:
            return Task.objects.none()
        return (
            Task.objects.filter(project=project, parent_task=None)
            .select_related("assigned_to", "created_by", "project")
            .prefetch_related("comments")
        )

    def create(self, request, *args, **kwargs):
        project = _get_accessible_project(request.user, self.kwargs["project_id"])
        if not project:
            return Response(
                {"success": False, "error": {"message": "Project not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(data={**request.data, "project": project.id}, context={"request": request})
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        TaskActivity.objects.create(task=task, actor=request.user, action="created")
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_201_CREATED)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/tasks/<id>/"""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Task.objects.all()
        return Task.objects.filter(
            Q(project__owner=user) | Q(project__members=user)
        ).distinct()

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        instance = self.get_object()
        old_status = instance.status
        response = super().update(request, *args, **kwargs)
        instance.refresh_from_db()
        if instance.status != old_status:
            TaskActivity.objects.create(
                task=instance,
                actor=request.user,
                action="status_changed",
                old_value=old_status,
                new_value=instance.status,
            )
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"success": True, "message": "Task deleted."}, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_task_status(request, pk):
    """PATCH /api/v1/tasks/<id>/status/ — real-time status update endpoint."""
    user = request.user
    try:
        if user.is_admin:
            task = Task.objects.get(pk=pk)
        else:
            task = Task.objects.get(
                Q(pk=pk) & (Q(project__owner=user) | Q(project__members=user))
            )
    except Task.DoesNotExist:
        return Response(
            {"success": False, "error": {"message": "Task not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = TaskStatusUpdateSerializer(task, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    old_status = task.status
    task = serializer.save()

    if task.status != old_status:
        TaskActivity.objects.create(
            task=task,
            actor=user,
            action="status_changed",
            old_value=old_status,
            new_value=task.status,
        )

    return Response({
        "success": True,
        "message": "Task status updated.",
        "data": {
            "id": task.id,
            "status": task.status,
            "updated_at": task.updated_at,
            "completed_at": task.completed_at,
        },
    })


class TaskCommentListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/v1/tasks/<task_id>/comments/"""
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]

    def _get_task(self):
        user = self.request.user
        task_id = self.kwargs["task_id"]
        if user.is_admin:
            return Task.objects.get(pk=task_id)
        return Task.objects.get(
            Q(pk=task_id) & (Q(project__owner=user) | Q(project__members=user))
        )

    def get_queryset(self):
        task = self._get_task()
        return task.comments.select_related("author")

    def perform_create(self, serializer):
        task = self._get_task()
        serializer.save(task=task, author=self.request.user)


class TaskActivityView(generics.ListAPIView):
    """GET /api/v1/tasks/<task_id>/activity/ — audit log."""
    serializer_class = TaskActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TaskActivity.objects.filter(task_id=self.kwargs["task_id"]).select_related("actor")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_tasks(request):
    """GET /api/v1/tasks/me/ — tasks assigned to current user."""
    user = request.user
    status_filter = request.query_params.get("status")
    qs = Task.objects.filter(assigned_to=user).select_related("project", "created_by")
    if status_filter:
        qs = qs.filter(status=status_filter)
    from .serializers import TaskSerializer
    serializer = TaskSerializer(qs, many=True, context={"request": request})
    return Response({"success": True, "count": qs.count(), "results": serializer.data})
