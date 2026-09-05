from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db.models import TextChoices
from django.db.models.constraints import CheckConstraint
from django.db.models.deletion import CASCADE
from django.db.models.expressions import F
from django.db.models.fields import BooleanField, CharField
from django.db.models.fields.files import ImageField
from django.db.models.fields.related import ForeignKey
from django.db.models.query_utils import Q

from .base import BaseModel


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("The Phone number must be set")
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    class Role(TextChoices):
        USER = "user", "Oddiy foydalanuvchi"
        ADMIN = "admin", "Admin"
        SUPER_ADMIN = "super_admin", "Super admin"

    phone = CharField(max_length=15, unique=True)
    full_name = CharField(max_length=255, blank=True)
    avatar = ImageField(upload_to="avatars/", null=True, blank=True)
    is_verified = BooleanField(default=False)
    is_vip = BooleanField(default=False)
    role = CharField(max_length=20, choices=Role.choices, default=Role.USER)
    language = CharField(max_length=5, default="uz")
    dark_mode = BooleanField(default=False)
    is_staff = BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if self.role == self.Role.SUPER_ADMIN:
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)

    @property
    def active_subscription(self):
        return self.subscriptions.filter(is_active=True).order_by("-started_at").first()

    @property
    def current_plan(self):
        sub = self.active_subscription
        return sub.plan if sub else None


class Follow(BaseModel):
    follower = ForeignKey(User, CASCADE, related_name="following")
    following = ForeignKey(User, CASCADE, related_name="followers")

    class Meta:
        unique_together = ("follower", "following")
        constraints = [
            CheckConstraint(
                condition=~Q(follower=F("following")), name="cannot_follow_self"
            )
        ]
