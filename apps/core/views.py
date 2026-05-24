from django.shortcuts import render


def index(request):
    return render(request, "core/landing.html")


def dashboard(request):
    return render(request, "core/dashboard.html")


def login_page(request):
    return render(request, "accounts/login.html")


def register_page(request):
    return render(request, "accounts/register.html")


def projects_page(request):
    return render(request, "projects/list.html")


def project_detail_page(request, pk):
    return render(request, "projects/detail.html", {"project_id": pk})
