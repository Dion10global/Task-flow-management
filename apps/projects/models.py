from django.conf import settings
from django.db import models
from django.utils import timezone


class Project(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"
        COMPLETED = "completed", "Completed"

    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ProjectMember",
        related_name="projects",
        blank=True,
    )
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return self.name


class ProjectMember(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MANAGER = "manager", "Manager"
        CONTRIBUTOR = "contributor", "Contributor"
        VIEWER = "viewer", "Viewer"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CONTRIBUTOR)
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "project_members"
        unique_together = [["project", "user"]]
        indexes = [
            models.Index(fields=["project", "user"]),
        ]

    def __str__(self):
        return f"{self.user} → {self.project} ({self.role})"
