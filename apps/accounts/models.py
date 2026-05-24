import uuid
import random
import string
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", False)  # inactive until OTP verified
        user = self.model(email=email, **extra_fields)
        user.set_unusable_password()  # passwordless — auth is via OTP only
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("role", "admin")
        user = self.create_user(email, **extra_fields)
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN  = "admin",  "Admin"
        MEMBER = "member", "Member"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email       = models.EmailField(unique=True, db_index=True)
    first_name  = models.CharField(max_length=150)
    last_name   = models.CharField(max_length=150)
    role        = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    avatar      = models.ImageField(upload_to="avatars/", null=True, blank=True)
    is_active   = models.BooleanField(default=False)   # activated after OTP verify
    is_verified = models.BooleanField(default=False)   # email OTP confirmed
    is_staff    = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login  = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["email"]
        indexes  = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN


class OTP(models.Model):
    """One-Time Password for email verification and password reset."""

    class Purpose(models.TextChoices):
        REGISTER       = "register",       "Register"
        PASSWORD_RESET = "password_reset", "Password Reset"
        LOGIN          = "login",          "Login"

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    code       = models.CharField(max_length=6)
    purpose    = models.CharField(max_length=20, choices=Purpose.choices)
    is_used    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "otps"
        ordering = ["-created_at"]
        indexes  = [models.Index(fields=["user", "purpose", "is_used"])]

    def save(self, *args, **kwargs):
        if not self.pk:
            expiry = getattr(settings, "OTP_EXPIRY_MINUTES", 10)
            self.expires_at = timezone.now() + timedelta(minutes=expiry)
            self.code = "".join(random.choices(string.digits, k=6))
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired

    def __str__(self):
        return f"OTP({self.purpose}) for {self.user.email} — {'used' if self.is_used else 'active'}"
