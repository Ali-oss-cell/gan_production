# Generated manually for account type data migration

from django.db import migrations


def migrate_account_types(apps, schema_editor):
    """
    Migrate existing gold and silver users to premium account type.
    """
    TalentUserProfile = apps.get_model('profiles', 'TalentUserProfile')
    
    # Convert gold users to premium
    TalentUserProfile.objects.filter(account_type='gold').update(account_type='premium')
    
    # Convert silver users to premium
    TalentUserProfile.objects.filter(account_type='silver').update(account_type='premium')


def reverse_migrate_account_types(apps, schema_editor):
    """
    Reverse migration - convert premium users back to gold (as a fallback).
    Note: This is not perfect as we can't distinguish between original gold and silver users.
    """
    TalentUserProfile = apps.get_model('profiles', 'TalentUserProfile')
    
    # Convert premium users back to gold (we can't distinguish original gold vs silver)
    TalentUserProfile.objects.filter(account_type='premium').update(account_type='gold')


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0020_update_account_types'),
    ]

    operations = [
        migrations.RunPython(
            code=migrate_account_types,
            reverse_code=reverse_migrate_account_types,
        ),
    ]
