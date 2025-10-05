# Generated manually for zipcode removal

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0021_migrate_account_types'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='talentuserprofile',
            name='zipcode',
        ),
    ]
