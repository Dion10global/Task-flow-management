import bleach
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Project, ProjectMember
from apps.accounts.serializers import UserPublicSerializer

User = get_user_model()


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = ProjectMember
        fields = ["id", "user", "user_id", "role", "joined_at"]
        read_only_fields = ["id", "joined_at"]


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserPublicSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id", "name", "description", "status", "owner",
            "deadline", "member_count", "task_count",
            "completion_percentage", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def validate_name(self, value):
        return bleach.clean(value.strip())

    def validate_description(self, value):
        return bleach.clean(value.strip())

    def get_member_count(self, obj):
        return obj.memberships.count()

    def get_task_count(self, obj):
        return obj.tasks.count()

    def get_completion_percentage(self, obj):
        total = obj.tasks.count()
        if not total:
            return 0
        done = obj.tasks.filter(status="done").count()
        return round((done / total) * 100, 1)


class ProjectCreateSerializer(serializers.ModelSerializer):
    member_emails = serializers.ListField(
        child=serializers.EmailField(),
        write_only=True,
        required=False,
        default=list,
    )

    class Meta:
        model = Project
        fields = ["name", "description", "status", "deadline", "member_emails"]

    def validate_name(self, value):
        return bleach.clean(value.strip())

    def validate_description(self, value):
        return bleach.clean(value.strip())

    def create(self, validated_data):
        member_emails = validated_data.pop("member_emails", [])
        request = self.context["request"]
        project = Project.objects.create(owner=request.user, **validated_data)
        # Add owner as a member
        ProjectMember.objects.create(project=project, user=request.user, role=ProjectMember.Role.OWNER)
        # Add additional members
        for email in member_emails:
            try:
                user = User.objects.get(email=email)
                ProjectMember.objects.get_or_create(
                    project=project, user=user,
                    defaults={"role": ProjectMember.Role.CONTRIBUTOR},
                )
            except User.DoesNotExist:
                pass  # Silently skip unknown emails
        return project
