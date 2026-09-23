"""Abstract base models shared across the project.

These are not database tables themselves. Other models inherit from them
to get UUID primary keys, timestamps, and soft deletion.
"""

import uuid

from django.db import models
from django.utils import timezone


class UUIDModel(models.Model):
    """Primary key is a random UUID, so IDs in URLs cannot be guessed."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Records when a row was created and last changed."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    """Queryset that understands soft deletion."""

    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)

    def delete(self):
        """Soft-delete every row in this queryset."""
        return self.update(deleted_at=timezone.now())

    def hard_delete(self):
        """Permanently remove rows. Reserved for owners."""
        return super().delete()


class SoftDeleteManager(models.Manager):
    """Default manager: hides soft-deleted rows."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class AllObjectsManager(models.Manager):
    """Secondary manager: includes soft-deleted rows, for restore and audit."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(models.Model):
    """
    Deletion sets a timestamp instead of removing the row.

    This protects against accidental data loss: a deleted assessment can be
    restored, and nothing disappears from the audit trail.
    """

    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class BaseModel(UUIDModel, TimeStampedModel):
    """Most models inherit this: UUID key plus timestamps."""

    class Meta:
        abstract = True