import bleach
from rest_framework import serializers
from apps.accounts.serializers import UserPublicSerializer
from .models import Task, TaskComment, TaskActivity


class TaskCommentSerializer(serializers.ModelSerializer):
    author = UserPublicSerializer(read_only=True)

    class Meta:
        model = TaskComment
        fields = ["id", "author", "body", "created_at", "updated_at"]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def validate_body(self, value):
        return bleach.clean(value.strip())


class TaskActivitySerializer(serializers.ModelSerializer):
    actor = UserPublicSerializer(read_only=True)

    class Meta:
        model = TaskActivity
        fields = ["id", "actor", "action", "old_value", "new_value", "timestamp"]
        read_only_fields = fields


class TaskSerializer(serializers.ModelSerializer):
    assigned_to = UserPublicSerializer(read_only=True)
    assigned_to_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    created_by = UserPublicSerializer(read_only=True)
    comment_count = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "status", "priority",
            "project", "assigned_to", "assigned_to_id", "created_by",
            "parent_task", "due_date", "estimated_hours", "actual_hours",
            "tags", "comment_count", "is_overdue",
            "created_at", "updated_at", "completed_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at", "completed_at"]

    def validate_title(self, value):
        return bleach.clean(value.strip())

    def validate_description(self, value):
        return bleach.clean(value.strip())

    def validate_tags(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list.")
        return [bleach.clean(str(t).strip()) for t in value[:10]]

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_is_overdue(self, obj):
        if not obj.due_date or obj.status in (Task.Status.DONE, Task.Status.CANCELLED):
            return False
        from django.utils import timezone
        return obj.due_date < timezone.now().date()

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    """Lightweight serializer for real-time status updates."""
    class Meta:
        model = Task
        fields = ["status"]

    def validate_status(self, value):
        valid = [c[0] for c in Task.Status.choices]
        if value not in valid:
            raise serializers.ValidationError(f"Status must be one of: {valid}")
        return value
