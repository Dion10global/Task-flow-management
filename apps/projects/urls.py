from django.urls import path
from . import views

urlpatterns = [
    path("projects/", views.ProjectListCreateView.as_view(), name="project-list-create"),
    path("projects/<int:pk>/", views.ProjectDetailView.as_view(), name="project-detail"),
    path("projects/<int:project_id>/members/", views.ProjectMemberListView.as_view(), name="project-members"),
    path("projects/<int:project_id>/members/<int:pk>/", views.ProjectMemberDetailView.as_view(), name="project-member-detail"),
    path("projects/<int:project_id>/stats/", views.project_stats, name="project-stats"),
]
