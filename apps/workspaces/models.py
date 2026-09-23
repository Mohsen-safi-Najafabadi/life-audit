"""Workspaces isolate data; memberships grant access to them."""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Workspace(BaseModel):
    """
    The isolation boundary. Every piece of tracked data belongs to exactly
    one workspace, and access is only ever granted through a Membership.
    """

    name = models.CharField(_("name"), max_length=120)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_workspaces",
        verbose_name=_("owner"),
    )
    timezone = models.CharField(_("timezone"), max_length=64, default="Europe/Berlin")

    class Meta:
        verbose_name = _("workspace")
        verbose_name_plural = _("workspaces")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def role_of(self, user):
        """Return this user's role here, or None if they have no access."""
        if not user or not user.is_authenticated:
            return None
        membership = self.memberships.filter(
            user=user, accepted_at__isnull=False
        ).first()
        return membership.role if membership else None

    def can_view(self, user):
        return self.role_of(user) is not None

    def can_edit(self, user):
        return self.role_of(user) in (Membership.Role.OWNER, Membership.Role.EDITOR)

    def can_administer(self, user):
        return self.role_of(user) == Membership.Role.OWNER


class Membership(BaseModel):
    """
    Grants one user one role in one workspace.

    Access is never derived from a URL. It is derived from a row in this
    table, checked on the server for every request.
    """

    class Role(models.TextChoices):
        OWNER = "owner", _("Owner")
        EDITOR = "editor", _("Editor")
        VIEWER = "viewer", _("Viewer")

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name=_("workspace"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name=_("user"),
    )
    role = models.CharField(
        _("role"), max_length=10, choices=Role.choices, default=Role.VIEWER
    )

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invitations",
        verbose_name=_("invited by"),
    )
    accepted_at = models.DateTimeField(_("accepted at"), null=True, blank=True)

    class Meta:
        verbose_name = _("membership")
        verbose_name_plural = _("memberships")
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "user"], name="unique_membership_per_workspace"
            )
        ]
        ordering = ["workspace", "role"]

    def __str__(self):
        return f"{self.user} — {self.get_role_display()} in {self.workspace}"

    @property
    def is_active(self):
        return self.accepted_at is not None