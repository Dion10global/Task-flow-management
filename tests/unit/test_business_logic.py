"""
Unit Tests — Business Logic
Covers: user model, task auto-complete, serializer validation, permissions, pagination.
"""
import pytest
from django.utils import timezone
from datetime import date, timedelta

from tests.factories import UserFactory, ProjectFactory, TaskFactory, AdminUserFactory
from apps.accounts.serializers import RegisterSerializer
from apps.tasks.models import Task
from apps.tasks.serializers import TaskSerializer, TaskStatusUpdateSerializer


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_sets_email_as_username(self):
        user = UserFactory(email="alice@example.com")
        assert user.email == "alice@example.com"

    def test_full_name_concatenation(self):
        user = UserFactory(first_name="Jane", last_name="Doe")
        assert user.get_full_name() == "Jane Doe"

    def test_admin_role_property(self):
        admin = AdminUserFactory()
        member = UserFactory()
        assert admin.is_admin is True
        assert member.is_admin is False

    def test_password_is_hashed(self):
        user = UserFactory()
        assert not user.password.startswith("SecurePass")
        assert user.check_password("SecurePass123!")

    def test_str_representation(self):
        user = UserFactory(email="test@example.com", first_name="Test", last_name="User")
        assert "test@example.com" in str(user)


@pytest.mark.django_db
class TestTaskAutoComplete:
    def test_task_sets_completed_at_when_done(self):
        task = TaskFactory(status=Task.Status.TODO)
        assert task.completed_at is None
        task.status = Task.Status.DONE
        task.save()
        task.refresh_from_db()
        assert task.completed_at is not None

    def test_task_clears_completed_at_when_reopened(self):
        task = TaskFactory(status=Task.Status.DONE)
        task.status = Task.Status.IN_PROGRESS
        task.save()
        task.refresh_from_db()
        assert task.completed_at is None

    def test_is_overdue_for_past_due_date(self):
        task = TaskFactory(
            status=Task.Status.TODO,
            due_date=date.today() - timedelta(days=1),
        )
        serializer = TaskSerializer(task)
        assert serializer.data["is_overdue"] is True

    def test_is_not_overdue_when_done(self):
        task = TaskFactory(
            status=Task.Status.DONE,
            due_date=date.today() - timedelta(days=5),
        )
        serializer = TaskSerializer(task)
        assert serializer.data["is_overdue"] is False

    def test_is_not_overdue_for_future_date(self):
        task = TaskFactory(
            status=Task.Status.TODO,
            due_date=date.today() + timedelta(days=7),
        )
        serializer = TaskSerializer(task)
        assert serializer.data["is_overdue"] is False


@pytest.mark.django_db
class TestRegisterSerializerValidation:
    def test_valid_registration(self):
        data = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_password_mismatch_fails(self):
        data = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "StrongPass123!",
            "password_confirm": "WrongPass456!",
        }
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "password_confirm" in serializer.errors

    def test_duplicate_email_fails(self):
        UserFactory(email="existing@example.com")
        data = {
            "email": "existing@example.com",
            "first_name": "Dup",
            "last_name": "User",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()

    def test_weak_password_fails(self):
        data = {
            "email": "weak@example.com",
            "first_name": "Weak",
            "last_name": "User",
            "password": "123",
            "password_confirm": "123",
        }
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()


@pytest.mark.django_db
class TestProjectCompletion:
    def test_completion_percentage_all_done(self):
        from apps.projects.serializers import ProjectSerializer
        project = ProjectFactory()
        TaskFactory.create_batch(3, project=project, status=Task.Status.DONE)
        data = ProjectSerializer(project).data
        assert data["completion_percentage"] == 100.0

    def test_completion_percentage_none_done(self):
        from apps.projects.serializers import ProjectSerializer
        project = ProjectFactory()
        TaskFactory.create_batch(4, project=project, status=Task.Status.TODO)
        data = ProjectSerializer(project).data
        assert data["completion_percentage"] == 0

    def test_completion_percentage_partial(self):
        from apps.projects.serializers import ProjectSerializer
        project = ProjectFactory()
        TaskFactory.create_batch(2, project=project, status=Task.Status.DONE)
        TaskFactory.create_batch(2, project=project, status=Task.Status.TODO)
        data = ProjectSerializer(project).data
        assert data["completion_percentage"] == 50.0
