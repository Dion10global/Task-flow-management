import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from apps.projects.models import Project, ProjectMember
from apps.tasks.models import Task

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "SecurePass123!")
    is_active = True
    role = User.Role.MEMBER


class AdminUserFactory(UserFactory):
    role = User.Role.ADMIN
    is_staff = True


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Project {n}")
    description = factory.Faker("paragraph")
    status = Project.Status.ACTIVE
    owner = factory.SubFactory(UserFactory)


class ProjectMemberFactory(DjangoModelFactory):
    class Meta:
        model = ProjectMember

    project = factory.SubFactory(ProjectFactory)
    user = factory.SubFactory(UserFactory)
    role = ProjectMember.Role.CONTRIBUTOR


class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task

    title = factory.Sequence(lambda n: f"Task {n}")
    description = factory.Faker("sentence")
    status = Task.Status.TODO
    priority = Task.Priority.MEDIUM
    project = factory.SubFactory(ProjectFactory)
    created_by = factory.SubFactory(UserFactory)
