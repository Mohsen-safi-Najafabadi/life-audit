"""Custom user model: authentication by email address, not username."""

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Creates users with an email address as the identifier."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("A superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    A person who can sign in.

    The primary key is a UUID so that user identifiers appearing in URLs
    cannot be guessed or enumerated.
    """

    class Locale(models.TextChoices):
        PERSIAN = "fa", _("فارسی")
        GERMAN = "de", _("Deutsch")
        ENGLISH = "en", _("English")

    class Calendar(models.TextChoices):
        JALALI = "jalali", _("Jalali (Shamsi)")
        GREGORIAN = "gregorian", _("Gregorian")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(_("email address"), unique=True)
    display_name = models.CharField(_("display name"), max_length=150, blank=True)

    locale = models.CharField(
        _("language"), max_length=5, choices=Locale.choices, default=Locale.PERSIAN
    )
    calendar = models.CharField(
        _("calendar"), max_length=10, choices=Calendar.choices, default=Calendar.JALALI
    )

    # Django requires these two for the admin site and permissions.
    is_staff = models.BooleanField(_("staff status"), default=False)
    is_active = models.BooleanField(_("active"), default=True)

    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["email"]

    def __str__(self):
        return self.email

    def get_short_name(self):
        return self.display_name or self.email.split("@")[0]

    def get_full_name(self):
        return self.display_name or self.email