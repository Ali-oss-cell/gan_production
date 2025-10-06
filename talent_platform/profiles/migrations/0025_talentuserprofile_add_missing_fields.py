# Generated manually to add missing fields to TalentUserProfile

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0024_alter_talentuserprofile_date_of_birth'),
    ]

    operations = [
        migrations.AddField(
            model_name='talentuserprofile',
            name='city',
            field=models.CharField(blank=True, db_index=True, default='', max_length=25),
        ),
        migrations.AddField(
            model_name='talentuserprofile',
            name='phone',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='talentuserprofile',
            name='gender',
            field=models.CharField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], db_index=True, default='Male', max_length=10),
        ),
    ]
