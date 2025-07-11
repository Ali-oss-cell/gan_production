# Generated manually

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from django.utils import timezone

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('payments', '0004_alter_paymenttransaction_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RestrictedCountryUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('country', models.CharField(max_length=50)),
                ('is_approved', models.BooleanField(default=False)),
                ('account_type', models.CharField(default='free', max_length=20)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='restricted_country_updates', to=settings.AUTH_USER_MODEL)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='restricted_country_status', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Restricted Country User',
                'verbose_name_plural': 'Restricted Country Users',
                'ordering': ['-created_at'],
            },
        ),
    ]