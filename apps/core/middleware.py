from django.conf import settings


class SecurityHeadersMiddleware:
    """
    Add security headers to every HTTP response.
    In DEBUG mode only safe, non-redirecting headers are applied.
    HSTS is never set here — Django's SECURE_HSTS_SECONDS handles that
    in production only.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # ── Always safe — apply in both dev and prod ────────────
        response["X-Content-Type-Options"] = "nosniff"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # ── Production-only headers ─────────────────────────────
        if not settings.DEBUG:
            response["X-Frame-Options"] = "DENY"
            response["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
            # NOTE: Never set Strict-Transport-Security here.
            # Use Django's SECURE_HSTS_SECONDS in settings instead.

        return response
