from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


DEFAULT_COLUMNS = [
    "id",
    "name",
    "type",
    "status",
    "vendor",
    "custodian",
    "description",
    "added",
    "updated",
]


def seed_grid_settings(apps, schema_editor):
    GridColumnSettings = apps.get_model("inventory", "GridColumnSettings")
    GridColumnSettings.objects.get_or_create(
        pk=1, defaults={"allowed_columns": DEFAULT_COLUMNS}
    )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("inventory", "0016_groupprofile_is_engineer"),
    ]

    operations = [
        migrations.CreateModel(
            name="GridColumnSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "allowed_columns",
                    models.JSONField(blank=True, default=list),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "grid column settings",
                "verbose_name_plural": "grid column settings",
            },
        ),
        migrations.CreateModel(
            name="UserColumnPreference",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "visible_columns",
                    models.JSONField(blank=True, null=True),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="grid_column_preference",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "user column preference",
                "verbose_name_plural": "user column preferences",
            },
        ),
        migrations.RunPython(seed_grid_settings, migrations.RunPython.noop),
    ]
