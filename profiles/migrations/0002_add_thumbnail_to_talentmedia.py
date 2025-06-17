from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='talentmedia',
            name='thumbnail',
            field=models.ImageField(upload_to='thumbnails/', blank=True, null=True),
        ),
    ] 