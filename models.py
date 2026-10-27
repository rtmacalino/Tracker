from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.urls import reverse

from .grid import default_allowed_columns


class AssetType(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AssetTypeStatus(models.Model):
    asset_type = models.ForeignKey(
        AssetType, on_delete=models.CASCADE, related_name="statuses"
    )
    key = models.SlugField(max_length=30, help_text="Stored value, e.g. available")
    label = models.CharField(max_length=60, help_text="Shown in the status menu")
    is_default = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "key"]
        unique_together = [("asset_type", "key")]
        verbose_name_plural = "statuses"

    def __str__(self):
        return f"{self.asset_type.name}: {self.label}"


class GroupProfile(models.Model):
    """Extra settings for an auth Group. Vendor groups have is_vendor=True."""

    group = models.OneToOneField(
        "auth.Group",
        on_delete=models.CASCADE,
        related_name="profile",
    )
    is_vendor = models.BooleanField("Vendor", default=False)
    is_engineer = models.BooleanField("Engineer", default=False)

    class Meta:
        verbose_name = "group profile"
        verbose_name_plural = "group profiles"

    def __str__(self):
        return self.group.name


class GridColumnSettings(models.Model):
    """The single Admin/Engineer-managed set of columns users may show."""

    allowed_columns = models.JSONField(default=list, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "grid column settings"
        verbose_name_plural = "grid column settings"

    def __str__(self):
        return "Grid column settings"

    @classmethod
    def load(cls):
        row, _ = cls.objects.get_or_create(
            pk=1, defaults={"allowed_columns": default_allowed_columns()}
        )
        # Ensure all default columns are present and in catalog order
        current = set(row.allowed_columns or [])
        defaults = set(default_allowed_columns())
        if current != defaults:
            merged = [c for c in default_allowed_columns() if c in current or c in defaults]
            row.allowed_columns = merged
            row.save(update_fields=["allowed_columns"])
        return row


class UserColumnPreference(models.Model):
    """Per-user visible columns. A null value means "use the role default"."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grid_column_preference",
    )
    visible_columns = models.JSONField(null=True, blank=True)
    column_order = models.JSONField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "user column preference"
        verbose_name_plural = "user column preferences"

    def __str__(self):
        return f"Columns for {self.user}"


class Asset(models.Model):
    """Shared columns. Each concrete type lives in its own table (MTI)."""

    class Status(models.TextChoices):
        IN_USE = "in_use", "In use"
        IN_STORAGE = "in_storage", "In storage"
        MAINTENANCE = "maintenance", "Maintenance"
        RETIRED = "retired", "Retired"
        LOST = "lost", "Lost"

    name = models.CharField(max_length=160)
    asset_type = models.ForeignKey(
        AssetType,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="assets",
    )
    status = models.CharField(max_length=30, default=Status.IN_STORAGE)

    vendor = models.ForeignKey(
        "auth.Group",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assets",
        verbose_name="Vendor",
        help_text="Vendor that owns this record. Members of this group can see it.",
    )
    custodian = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="custodied_assets",
        help_text="Person accountable for the asset. They can always see this record.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="created_assets",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="updated_assets",
        help_text="User who last changed this record.",
    )

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("inventory:asset_detail", args=[self.pk])

    @property
    def status_slug(self):
        return self.status.replace("_", "-")

    @property
    def status_label(self):
        if self.asset_type_id:
            for row in self.asset_type.statuses.all():
                if row.key == self.status:
                    return row.label
        return dict(self.Status.choices).get(self.status, self.status)

    @property
    def scope_label(self):
        parts = []
        if self.vendor:
            parts.append(self.vendor.name)
        if self.custodian:
            parts.append(self.custodian.get_username())
        return " / ".join(parts) if parts else "Unassigned"


class FTTB(Asset):
    """Fiber to the building. Type-specific columns land here later."""

    TYPE_NAME = "FTTB"

    class Meta:
        verbose_name = "FTTB"
        verbose_name_plural = "FTTB"


class OLT(Asset):
    """Optical line terminal. Type-specific columns land here later."""

    TYPE_NAME = "OLT"

    class Meta:
        verbose_name = "OLT"
        verbose_name_plural = "OLT"


TYPE_MODELS = {
    FTTB.TYPE_NAME: FTTB,
    OLT.TYPE_NAME: OLT,
}


def resolve_asset(asset):
    """Return the concrete (child) instance when one exists."""
    if asset.asset_type_id:
        model = TYPE_MODELS.get(asset.asset_type.name)
        if model is not None:
            try:
                return getattr(asset, model._meta.model_name)
            except model.DoesNotExist:
                return asset
    return asset


def status_options_for(asset_type):
    if asset_type is not None:
        rows = list(asset_type.statuses.all())
        if rows:
            return [(row.key, row.label) for row in rows]
    return list(Asset.Status.choices)


def default_status_for(asset_type):
    if asset_type is not None:
        rows = list(asset_type.statuses.all())
        if rows:
            for row in rows:
                if row.is_default:
                    return row.key
            return rows[0].key
    return Asset.Status.IN_STORAGE


def all_status_options():
    options = list(Asset.Status.choices)
    seen = {key for key, _ in options}
    for row in AssetTypeStatus.objects.order_by("label"):
        if row.key not in seen:
            options.append((row.key, row.label))
            seen.add(row.key)
    return options