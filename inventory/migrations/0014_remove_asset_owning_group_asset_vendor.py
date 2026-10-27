import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('inventory', '0013_remove_asset_vendor'),
    ]

    operations = [
        migrations.RenameField(
            model_name='asset',
            old_name='owning_group',
            new_name='vendor',
        ),
        migrations.AlterField(
            model_name='asset',
            name='vendor',
            field=models.ForeignKey(
                blank=True,
                help_text='Vendor that owns this record. Members of this group can see it.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assets',
                to='auth.group',
                verbose_name='Vendor',
            ),
        ),
    ]
