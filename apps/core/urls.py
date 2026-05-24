from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("login/", views.login_page, name="login"),
    path("register/", views.register_page, name="register"),
    path("projects/", views.projects_page, name="projects"),
    path("projects/<int:pk>/", views.project_detail_page, name="project-detail"),
]
