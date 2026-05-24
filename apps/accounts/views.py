import logging
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTP
from .emails import send_otp_email
from .serializers import (
    RegisterInitSerializer, RegisterVerifySerializer,
    LoginRequestSerializer, LoginVerifySerializer,
    UserPublicSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthThrottle(AnonRateThrottle):
    rate  = "10/minute"
    scope = "auth"


def _issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    refresh["email"]     = user.email
    refresh["role"]      = user.role
    refresh["full_name"] = user.get_full_name()
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def _get_or_create_pending_user(email, first_name, last_name):
    user, created = User.objects.get_or_create(
        email=email,
        defaults={"first_name": first_name, "last_name": last_name, "is_active": False},
    )
    if not created and not user.is_verified:
        user.first_name = first_name
        user.last_name  = last_name
        user.save(update_fields=["first_name", "last_name"])
    return user


def _create_and_send_otp(user, purpose):
    """Invalidate old OTPs and create a fresh one. Returns (otp, email_sent, error)."""
    OTP.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)
    otp = OTP.objects.create(user=user, purpose=purpose)
    email_sent = False
    error = None
    try:
        send_otp_email(user, otp.code, purpose)
        email_sent = True
    except Exception as e:
        error = str(e)
        logger.error("Failed to send OTP email to %s: %s", user.email, e)
    return otp, email_sent, error


# ── REGISTER ─────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def register_init(request):
    """POST /api/v1/auth/register/ — collect details, send OTP."""
    ser = RegisterInitSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    user = _get_or_create_pending_user(d["email"], d["first_name"], d["last_name"])

    if user.is_verified:
        return Response(
            {"success": False, "error": {"message": "This email is already registered. Please log in."}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    otp, email_sent, error = _create_and_send_otp(user, OTP.Purpose.REGISTER)

    response_data = {"success": True, "email": d["email"]}

    if email_sent:
        response_data["message"] = (
            f"A 6-digit verification code has been sent to {d['email']}. "
            f"It expires in {getattr(settings, 'OTP_EXPIRY_MINUTES', 10)} minutes."
        )
    else:
        if settings.DEBUG:
            response_data["message"] = f"Email delivery failed ({error}). DEV MODE — your OTP is: {otp.code}"
            response_data["dev_otp"] = otp.code
        else:
            return Response(
                {"success": False, "error": {"message": f"Failed to send verification email. Please try again. ({error})"}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def register_verify(request):
    """POST /api/v1/auth/register/verify/ — verify OTP, activate account."""
    ser = RegisterVerifySerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    try:
        user = User.objects.get(email=d["email"], is_verified=False)
    except User.DoesNotExist:
        return Response(
            {"success": False, "error": {"message": "No pending registration found for this email."}},
            status=status.HTTP_404_NOT_FOUND,
        )

    otp = OTP.objects.filter(
        user=user, purpose=OTP.Purpose.REGISTER, is_used=False, code=d["otp"]
    ).order_by("-created_at").first()

    if not otp:
        return Response(
            {"success": False, "error": {"message": "Invalid OTP code. Please check and try again."}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if otp.is_expired:
        return Response(
            {"success": False, "error": {"message": "OTP has expired. Please request a new one."}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    otp.is_used      = True
    otp.save()
    user.is_active   = True
    user.is_verified = True
    user.save()

    tokens = _issue_tokens(user)
    return Response({
        "success": True,
        "message": "Account verified! Welcome to TaskFlow 🎉",
        "user":    UserPublicSerializer(user).data,
        "tokens":  tokens,
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def register_resend_otp(request):
    """POST /api/v1/auth/register/resend-otp/"""
    email = request.data.get("email", "").strip().lower()
    if not email:
        return Response({"success": False, "error": {"message": "Email is required."}}, status=400)
    try:
        user = User.objects.get(email=email, is_verified=False)
    except User.DoesNotExist:
        return Response({"success": False, "error": {"message": "No pending registration for this email."}}, status=404)

    otp, email_sent, error = _create_and_send_otp(user, OTP.Purpose.REGISTER)

    if email_sent:
        return Response({"success": True, "message": f"New OTP sent to {email}."})
    if settings.DEBUG:
        return Response({"success": True, "message": f"Email failed. DEV OTP: {otp.code}", "dev_otp": otp.code})
    return Response({"success": False, "error": {"message": f"Failed to send email: {error}"}}, status=500)


# ── LOGIN (OTP-based, passwordless) ──────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def login_request(request):
    """POST /api/v1/auth/login/ — send OTP to registered email."""
    ser = LoginRequestSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    email = ser.validated_data["email"].lower()

    try:
        user = User.objects.get(email=email, is_verified=True, is_active=True)
        otp, email_sent, error = _create_and_send_otp(user, OTP.Purpose.LOGIN)
        if not email_sent and settings.DEBUG:
            return Response({
                "success": True,
                "message": f"Email failed. DEV OTP: {otp.code}",
                "dev_otp": otp.code,
            })
    except User.DoesNotExist:
        pass  # Never reveal whether email is registered

    return Response({
        "success": True,
        "message": "If that email is registered, a sign-in code has been sent.",
    })


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def login_verify(request):
    """POST /api/v1/auth/login/verify/ — verify OTP → JWT tokens."""
    ser = LoginVerifySerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data

    try:
        user = User.objects.get(email=d["email"].lower(), is_verified=True, is_active=True)
    except User.DoesNotExist:
        return Response(
            {"success": False, "error": {"message": "Invalid or expired code."}},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    otp = OTP.objects.filter(
        user=user, purpose=OTP.Purpose.LOGIN, is_used=False, code=d["otp"]
    ).order_by("-created_at").first()

    if not otp or not otp.is_valid:
        return Response(
            {"success": False, "error": {"message": "Invalid or expired code."}},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    otp.is_used = True
    otp.save()
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    tokens = _issue_tokens(user)
    return Response({
        "success": True,
        "user":    UserPublicSerializer(user).data,
        "access":  tokens["access"],
        "refresh": tokens["refresh"],
    })


# ── LOGOUT ────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        RefreshToken(request.data.get("refresh")).blacklist()
    except Exception:
        pass
    return Response({"success": True, "message": "Logged out successfully."})


# ── ME ────────────────────────────────────────────────────────────

class MeView(generics.RetrieveUpdateAPIView):
    serializer_class   = UserPublicSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)
