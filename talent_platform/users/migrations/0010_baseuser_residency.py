# Generated manually to add residency field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_remove_token_add_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseuser',
            name='residency',
            field=models.CharField(blank=True, help_text='Country of residence', max_length=25),
        ),
    ]
