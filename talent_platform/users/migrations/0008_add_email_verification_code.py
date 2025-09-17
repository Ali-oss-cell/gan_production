# Generated migration for email verification code field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_baseuser_last_verification_email_sent'),  # Update this to your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='baseuser',
            name='email_verification_code',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]
