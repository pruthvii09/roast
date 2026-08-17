import uuid

from django.db import models
from django.utils import timezone


class TimeStampedUUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    """Default manager: only rows that have not been soft-deleted."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class AllObjectsManager(models.Manager):
    """Unfiltered manager for admin/internal use where dead rows matter."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])
