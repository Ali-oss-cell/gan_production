# Migration to remove link-based verification and keep only code-based

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_add_email_verification_code'),
    ]

    operations = [
        # Remove old token-based fields
        migrations.RemoveField(
            model_name='baseuser',
            name='email_verification_token',
        ),
        migrations.RemoveField(
            model_name='baseuser',
            name='email_verification_token_created',
        ),
        # Add new code-based timestamp field
        migrations.AddField(
            model_name='baseuser',
            name='email_verification_code_created',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
