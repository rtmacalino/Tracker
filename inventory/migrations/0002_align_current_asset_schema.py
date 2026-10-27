# Generated for the current inventory models. This migration replaces the
# legacy Category/Location/Asset schema with the current typed asset schema.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AssetType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("description", models.CharField(blank=True, max_length=255)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.RemoveField(model_name="asset", name="asset_tag"),
        migrations.RemoveField(model_name="asset", name="serial_number"),
        migrations.RemoveField(model_name="asset", name="assigned_to"),
        migrations.RemoveField(model_name="asset", name="purchase_date"),
        migrations.RemoveField(model_name="asset", name="purchase_cost"),
        migrations.RemoveField(model_name="asset", name="notes"),
        migrations.RemoveField(model_name="asset", name="category"),
        migrations.RemoveField(model_name="asset", name="location"),
        migrations.AlterField(
            model_name="asset",
            name="status",
            field=models.CharField(default="in_storage", max_length=30),
        ),
        migrations.AddField(
            model_name="asset",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="asset",
            name="asset_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="assets",
                to="inventory.assettype",
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="vendor",
            field=models.ForeignKey(
                blank=True,
                help_text="Vendor that owns this record. Members of this group can see it.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assets",
                to="auth.group",
                verbose_name="Vendor",
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="custodian",
            field=models.ForeignKey(
                blank=True,
                help_text="Person accountable for the asset. They can always see this record.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="custodied_assets",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_assets",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                help_text="User who last changed this record.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="updated_assets",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="AssetTypeStatus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.SlugField(help_text="Stored value, e.g. available", max_length=30)),
                ("label", models.CharField(help_text="Shown in the status menu", max_length=60)),
                ("is_default", models.BooleanField(default=False)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                ("asset_type", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="statuses", to="inventory.assettype")),
            ],
            options={
                "verbose_name_plural": "statuses",
                "ordering": ["order", "key"],
                "unique_together": {("asset_type", "key")},
            },
        ),
        migrations.CreateModel(
            name="GroupProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_vendor", models.BooleanField(default=False, verbose_name="Vendor")),
                ("is_engineer", models.BooleanField(default=False, verbose_name="Engineer")),
                ("group", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to="auth.group")),
            ],
            options={
                "verbose_name": "group profile",
                "verbose_name_plural": "group profiles",
            },
        ),
        migrations.CreateModel(
            name="GridColumnSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("allowed_columns", models.JSONField(blank=True, default=list)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("updated_by", models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "grid column settings",
                "verbose_name_plural": "grid column settings",
            },
        ),
        migrations.CreateModel(
            name="UserColumnPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("visible_columns", models.JSONField(blank=True, null=True)),
                ("column_order", models.JSONField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="grid_column_preference", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "user column preference",
                "verbose_name_plural": "user column preferences",
            },
        ),
        migrations.CreateModel(
            name="FTTB",
            fields=[
                ("asset_ptr", models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to="inventory.asset")),
            ],
            options={"verbose_name": "FTTB", "verbose_name_plural": "FTTB"},
            bases=("inventory.asset",),
        ),
        migrations.CreateModel(
            name="OLT",
            fields=[
                ("asset_ptr", models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to="inventory.asset")),
            ],
            options={"verbose_name": "OLT", "verbose_name_plural": "OLT"},
            bases=("inventory.asset",),
        ),
        migrations.DeleteModel(name="Category"),
        migrations.DeleteModel(name="Location"),
    ]
