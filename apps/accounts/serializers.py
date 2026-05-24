import bleach
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserPublicSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model  = User
        fields = ["id", "email", "first_name", "last_name", "full_name",
                  "role", "avatar", "is_verified", "date_joined"]
        read_only_fields = ["id", "date_joined", "role", "is_verified"]


# ── Step 1: Register (send OTP) ─────────────────────────────────
class RegisterInitSerializer(serializers.Serializer):
    email      = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name  = serializers.CharField(max_length=150)

    def validate_email(self, value):
        value = bleach.clean(value.strip().lower())
        if User.objects.filter(email=value, is_verified=True).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_first_name(self, value):
        return bleach.clean(value.strip())

    def validate_last_name(self, value):
        return bleach.clean(value.strip())


# ── Step 2: Verify OTP — no password ───────────────────────────
class RegisterVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp   = serializers.CharField(min_length=6, max_length=6)


# ── Login Step 1: request OTP ───────────────────────────────────
class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


# ── Login Step 2: verify OTP → JWT ─────────────────────────────
class LoginVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp   = serializers.CharField(min_length=6, max_length=6)


# ── JWT custom claims ───────────────────────────────────────────
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"]     = user.email
        token["role"]      = user.role
        token["full_name"] = user.get_full_name()
        return token
