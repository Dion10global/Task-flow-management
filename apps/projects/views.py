from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from .models import Project, ProjectMember
from .serializers import ProjectSerializer, ProjectCreateSerializer, ProjectMemberSerializer
from apps.accounts.permissions import IsAdmin, IsOwnerOrAdmin


class ProjectQuerysetMixin:
    """Restrict queryset to projects the current user has access to."""

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Project.objects.none()
        user = self.request.user
        if user.is_admin:
            return Project.objects.all().select_related("owner").prefetch_related("memberships__user")
        return (
            Project.objects.filter(
                Q(owner=user) | Q(members=user)
            )
            .distinct()
            .select_related("owner")
            .prefetch_related("memberships__user")
        )


class ProjectListCreateView(ProjectQuerysetMixin, generics.ListCreateAPIView):
    """
    GET  /api/v1/projects/       — list accessible projects
    POST /api/v1/projects/       — create a new project
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name", "deadline"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProjectCreateSerializer
        return ProjectSerializer

    @extend_schema(summary="List projects", responses={200: ProjectSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Create project", responses={201: ProjectSerializer})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        return Response(
            {"success": True, "data": ProjectSerializer(project).data},
            status=status.HTTP_201_CREATED,
        )


class ProjectDetailView(ProjectQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/projects/<id>/  — retrieve
    PATCH  /api/v1/projects/<id>/  — partial update
    DELETE /api/v1/projects/<id>/  — delete (admin/owner only)
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (request.user.is_admin or instance.owner == request.user):
            return Response(
                {"success": False, "error": {"message": "Only the project owner or an admin can delete this project."}},
                status=status.HTTP_403_FORBIDDEN,
            )
        self.perform_destroy(instance)
        return Response({"success": True, "message": "Project deleted."}, status=status.HTTP_200_OK)


class ProjectMemberListView(generics.ListCreateAPIView):
    """GET/POST /api/v1/projects/<project_id>/members/"""
    serializer_class = ProjectMemberSerializer
    permission_classes = [IsAuthenticated]

    def _get_project(self):
        user = self.request.user
        pk = self.kwargs["project_id"]
        if user.is_admin:
            return Project.objects.get(pk=pk)
        return Project.objects.get(Q(pk=pk) & (Q(owner=user) | Q(members=user)))

    def get_queryset(self):
        project = self._get_project()
        return project.memberships.select_related("user")

    def perform_create(self, serializer):
        project = self._get_project()
        serializer.save(project=project)


class ProjectMemberDetailView(generics.DestroyAPIView):
    """DELETE /api/v1/projects/<project_id>/members/<id>/ — remove a member."""
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return ProjectMember.objects.filter(project_id=self.kwargs["project_id"])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"success": True, "message": "Member removed from project."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def project_stats(request, project_id):
    """GET /api/v1/projects/<project_id>/stats/ — task breakdown."""
    user = request.user
    try:
        if user.is_admin:
            project = Project.objects.get(pk=project_id)
        else:
            project = Project.objects.get(
                Q(pk=project_id) & (Q(owner=user) | Q(members=user))
            )
    except Project.DoesNotExist:
        return Response(
            {"success": False, "error": {"message": "Project not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )

    tasks = project.tasks.all()
    stats = {
        "total": tasks.count(),
        "by_status": {
            "todo": tasks.filter(status="todo").count(),
            "in_progress": tasks.filter(status="in_progress").count(),
            "in_review": tasks.filter(status="in_review").count(),
            "done": tasks.filter(status="done").count(),
        },
        "by_priority": {
            "low": tasks.filter(priority="low").count(),
            "medium": tasks.filter(priority="medium").count(),
            "high": tasks.filter(priority="high").count(),
            "critical": tasks.filter(priority="critical").count(),
        },
        "overdue": tasks.filter(status__in=["todo", "in_progress"], due_date__lt=timezone.now().date()).count(),
        "completion_percentage": ProjectSerializer(project).data["completion_percentage"],
    }
    return Response({"success": True, "data": stats})
