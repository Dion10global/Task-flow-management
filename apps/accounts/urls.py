from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # ── Registration (2-step OTP) ──────────────────────────────
    path("register/",            views.register_init,       name="auth-register"),
    path("register/verify/",     views.register_verify,     name="auth-register-verify"),
    path("register/resend-otp/", views.register_resend_otp, name="auth-register-resend"),

    # ── Login / Logout ─────────────────────────────────────────
    path("login/",               views.login_request,        name="auth-login"),
    path("login/verify/",        views.login_verify,         name="auth-login-verify"),
    path("logout/",              views.logout_view,           name="auth-logout"),
    path("token/refresh/",       TokenRefreshView.as_view(), name="auth-token-refresh"),

    # ── Profile ────────────────────────────────────────────────
    path("me/",                  views.MeView.as_view(),    name="auth-me"),
]
