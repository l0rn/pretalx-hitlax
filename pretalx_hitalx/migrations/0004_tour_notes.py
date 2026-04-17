from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pretalx_hitalx', '0003_tour'),
    ]

    operations = [
        migrations.AddField(
            model_name='tour',
            name='notes',
            field=models.TextField(blank=True, default=''),
        ),
    ]
