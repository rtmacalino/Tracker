from django.db import migrations


def seed(apps, schema_editor):
    AssetType = apps.get_model("inventory", "AssetType")
    for name in ("FTTB", "OLT"):
        AssetType.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0010_fttb_olt_alter_assettypefield_unique_together_and_more")
    ]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
