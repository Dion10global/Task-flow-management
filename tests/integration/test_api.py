"""
Integration Tests — API Endpoints
Covers: auth, projects CRUD, tasks CRUD, status updates, RBAC.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status

from tests.factories import UserFactory, AdminUserFactory, ProjectFactory, TaskFactory, ProjectMemberFactory
from apps.tasks.models import Task


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def member_user(db):
    return UserFactory()


@pytest.fixture
def admin_user(db):
    return AdminUserFactory()


@pytest.fixture
def auth_client(api_client, member_user):
    response = api_client.post("/api/v1/auth/login/", {
        "email": member_user.email,
        "password": "SecurePass123!",
    })
    token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    response = api_client.post("/api/v1/auth/login/", {
        "email": admin_user.email,
        "password": "SecurePass123!",
    })
    token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


# ─── Auth Tests ────────────────────────────────────────────────
@pytest.mark.django_db
class TestAuth:
    def test_register_creates_user(self, api_client):
        res = api_client.post("/api/v1/auth/register/", {
            "email": "brand_new@example.com",
            "first_name": "Brand",
            "last_name": "New",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["success"] is True
        assert "tokens" in res.data

    def test_login_returns_tokens(self, api_client, member_user):
        res = api_client.post("/api/v1/auth/login/", {
            "email": member_user.email,
            "password": "SecurePass123!",
        })
        assert res.status_code == status.HTTP_200_OK
        assert "access" in res.data
        assert "refresh" in res.data

    def test_login_wrong_password_fails(self, api_client, member_user):
        res = api_client.post("/api/v1/auth/login/", {
            "email": member_user.email,
            "password": "WrongPassword!",
        })
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_returns_profile(self, auth_client, member_user):
        res = auth_client.get("/api/v1/auth/me/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["email"] == member_user.email

    def test_unauthenticated_me_rejected(self, api_client):
        res = api_client.get("/api/v1/auth/me/")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ─── Project Tests ─────────────────────────────────────────────
@pytest.mark.django_db
class TestProjects:
    def test_create_project(self, auth_client, member_user):
        res = auth_client.post("/api/v1/projects/", {
            "name": "My Project",
            "description": "A test project",
            "status": "active",
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["data"]["name"] == "My Project"

    def test_list_own_projects_only(self, auth_client, member_user):
        # Create a project that belongs to someone else
        other = UserFactory()
        ProjectFactory(owner=other)
        # Create user's own project
        ProjectFactory(owner=member_user)
        res = auth_client.get("/api/v1/projects/")
        assert res.status_code == status.HTTP_200_OK
        # User should only see their own project
        assert res.data["count"] == 1

    def test_admin_sees_all_projects(self, admin_client):
        ProjectFactory.create_batch(3)
        res = admin_client.get("/api/v1/projects/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["count"] >= 3

    def test_retrieve_project(self, auth_client, member_user):
        project = ProjectFactory(owner=member_user)
        res = auth_client.get(f"/api/v1/projects/{project.id}/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["name"] == project.name

    def test_member_cannot_access_unassigned_project(self, auth_client):
        other_project = ProjectFactory()
        res = auth_client.get(f"/api/v1/projects/{other_project.id}/")
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_project_as_owner(self, auth_client, member_user):
        project = ProjectFactory(owner=member_user)
        res = auth_client.delete(f"/api/v1/projects/{project.id}/")
        assert res.status_code == status.HTTP_200_OK


# ─── Task Tests ────────────────────────────────────────────────
@pytest.mark.django_db
class TestTasks:
    def test_create_task(self, auth_client, member_user):
        project = ProjectFactory(owner=member_user)
        res = auth_client.post(f"/api/v1/projects/{project.id}/tasks/", {
            "title": "New Task",
            "description": "Task description",
            "priority": "high",
            "project": project.id,
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["data"]["title"] == "New Task"

    def test_list_project_tasks(self, auth_client, member_user):
        project = ProjectFactory(owner=member_user)
        TaskFactory.create_batch(3, project=project)
        res = auth_client.get(f"/api/v1/projects/{project.id}/tasks/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["count"] == 3

    def test_update_task_status(self, auth_client, member_user):
        project = ProjectFactory(owner=member_user)
        task = TaskFactory(project=project, status=Task.Status.TODO)
        res = auth_client.patch(f"/api/v1/tasks/{task.id}/status/", {"status": "in_progress"})
        assert res.status_code == status.HTTP_200_OK
        assert res.data["data"]["status"] == "in_progress"

    def test_invalid_status_rejected(self, auth_client, member_user):
        project = ProjectFactory(owner=member_user)
        task = TaskFactory(project=project)
        res = auth_client.patch(f"/api/v1/tasks/{task.id}/status/", {"status": "flying"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_my_tasks_endpoint(self, auth_client, member_user):
        project = ProjectFactory(owner=member_user)
        TaskFactory.create_batch(2, project=project, assigned_to=member_user)
        TaskFactory(project=project)  # unassigned
        res = auth_client.get("/api/v1/tasks/me/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["count"] == 2
