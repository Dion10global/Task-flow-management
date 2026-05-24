from django.urls import path
from . import views

urlpatterns = [
    # Tasks within a project
    path("projects/<int:project_id>/tasks/", views.TaskListCreateView.as_view(), name="task-list-create"),

    # Individual task operations
    path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task-detail"),
    path("tasks/<int:pk>/status/", views.update_task_status, name="task-status-update"),

    # Comments & Activity
    path("tasks/<int:task_id>/comments/", views.TaskCommentListCreateView.as_view(), name="task-comments"),
    path("tasks/<int:task_id>/activity/", views.TaskActivityView.as_view(), name="task-activity"),

    # Current user's tasks
    path("tasks/me/", views.my_tasks, name="my-tasks"),
]
