"""The Life Audit itself: domains, dated assessments, and scores.

Every row here belongs to exactly one workspace. Access is granted only
through an accepted Membership, checked on the server.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel, SoftDeleteModel
from apps.workspaces.models import Workspace


class Cadence(models.TextChoices):
    """How often an area is worth re-rating.

    A 12-domain sheet is a quarterly instrument, but some areas move daily.
    Splitting by cadence keeps the daily form short and honest: rating
    'education' every evening would produce noise, not data.
    """

    DAILY = "daily", _("Daily")
    WEEKLY = "weekly", _("Weekly")
    MONTHLY = "monthly", _("Monthly")
    QUARTERLY = "quarterly", _("Quarterly")


class Domain(BaseModel):
    """One life area, e.g. sleep, work, finances.

    Domains are data, not code: they can be renamed, reordered, retired, or
    added without changing the application.
    """

    class Category(models.TextChoices):
        BODY = "body", _("Body")
        MIND = "mind", _("Mind")
        MATERIAL = "material", _("Practical / material")
        SOCIAL = "social", _("Social")

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="domains",
        verbose_name=_("workspace"),
    )

    name_fa = models.CharField(_("name (Persian)"), max_length=100)
    name_de = models.CharField(_("name (German)"), max_length=100, blank=True)
    name_en = models.CharField(_("name (English)"), max_length=100, blank=True)

    icon = models.CharField(_("icon"), max_length=40, blank=True)
    color = models.CharField(_("colour"), max_length=7, blank=True, default="#2F4F7F")

    category = models.CharField(
        _("category"), max_length=10, choices=Category.choices, default=Category.MIND
    )
    cadence = models.CharField(
        _("cadence"), max_length=10, choices=Cadence.choices, default=Cadence.QUARTERLY
    )

    sort_order = models.PositiveSmallIntegerField(_("sort order"), default=0)

    importance = models.PositiveSmallIntegerField(
        _("importance"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text=_(
            "Optional 0-10. Separates 'this is low and it matters' from "
            "'this is low and I do not mind'."
        ),
    )

    definition = models.TextField(
        _("definition"),
        blank=True,
        help_text=_(
            "What 0, 5 and 10 mean to you here. Writing this down keeps the "
            "scale stable over time instead of drifting with your mood."
        ),
    )

    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("domain")
        verbose_name_plural = _("domains")
        ordering = ["sort_order", "name_fa"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "name_fa"], name="unique_domain_name_per_workspace"
            )
        ]

    def __str__(self):
        return self.name_fa

    def label(self, locale="fa"):
        """The name in the requested language, falling back to Persian."""
        return {
            "fa": self.name_fa,
            "de": self.name_de or self.name_fa,
            "en": self.name_en or self.name_fa,
        }.get(locale, self.name_fa)


class Assessment(BaseModel, SoftDeleteModel):
    """One filled-in sheet, referring to one date.

    Deleting is soft: the row is flagged, never removed, so an accidental
    delete can be undone and the history stays intact.
    """

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="assessments",
        verbose_name=_("workspace"),
    )

    assessed_on = models.DateField(
        _("date"),
        db_index=True,
        help_text=_("The date this refers to, not the date it was typed in."),
    )
    cadence = models.CharField(
        _("cadence"), max_length=10, choices=Cadence.choices, default=Cadence.DAILY
    )

    note = models.TextField(
        _("note"),
        blank=True,
        help_text=_("What happened in this period. Explains the numbers later."),
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_assessments",
        verbose_name=_("created by"),
    )

    class Meta:
        verbose_name = _("assessment")
        verbose_name_plural = _("assessments")
        ordering = ["-assessed_on"]
        base_manager_name = "all_objects"
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "assessed_on", "cadence"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_live_assessment_per_date_and_cadence",
            )
        ]
        indexes = [
            models.Index(fields=["workspace", "-assessed_on"]),
        ]

    def __str__(self):
        return f"{self.assessed_on} ({self.get_cadence_display()})"

    @property
    def average(self):
        """Mean of this sheet's scores, or None when empty.

        A blunt number: it treats all domains as equally important and is
        only meaningful next to other averages from the same person.
        """
        values = [s.value for s in self.scores.all()]
        return round(sum(values) / len(values), 2) if values else None


class Score(BaseModel):
    """One rating: one domain, one assessment, 0-10."""

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="scores",
        verbose_name=_("assessment"),
    )
    domain = models.ForeignKey(
        Domain,
        on_delete=models.PROTECT,
        related_name="scores",
        verbose_name=_("domain"),
    )

    value = models.PositiveSmallIntegerField(
        _("score"),
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text=_("0 = very weak, 10 = excellent."),
    )
    target_value = models.PositiveSmallIntegerField(
        _("target"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )

    note = models.CharField(
        _("note"),
        max_length=300,
        blank=True,
        help_text=_("One line on why. Turns a number back into a reason later."),
    )

    class Meta:
        verbose_name = _("score")
        verbose_name_plural = _("scores")
        ordering = ["domain__sort_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "domain"], name="one_score_per_domain_per_assessment"
            ),
            models.CheckConstraint(
                condition=models.Q(value__gte=0) & models.Q(value__lte=10),
                name="score_value_between_0_and_10",
            ),
        ]

    def __str__(self):
        return f"{self.domain}: {self.value}"