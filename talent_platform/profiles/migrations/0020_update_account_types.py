# Generated manually for account type refactoring

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0019_alter_artisticmaterial_created_at_and_more'),
    ]

    operations = [
        # Update account type choices
        migrations.AlterField(
            model_name='talentuserprofile',
            name='account_type',
            field=models.CharField(
                choices=[
                    ('platinum', 'Platinum'),
                    ('premium', 'Premium'),
                    ('free', 'Free'),
                ],
                db_index=True,
                default='free',
                max_length=10
            ),
        ),
        # Data migration to convert existing gold/silver users to premium
        migrations.RunPython(
            code=migrations.RunPython.noop,  # We'll handle this in a separate data migration
            reverse_code=migrations.RunPython.noop,
        ),
    ]
