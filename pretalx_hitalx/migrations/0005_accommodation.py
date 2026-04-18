from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pretalx_hitalx', '0004_tour_notes'),
        ('event', '0029_event_domain'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Accommodation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('accommodation_type', models.CharField(blank=True, default='', max_length=100)),
                ('notes', models.TextField(blank=True, default='')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accommodations', to='event.event')),
            ],
        ),
        migrations.CreateModel(
            name='AccommodationBooking',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_date', models.DateField()),
                ('to_date', models.DateField()),
                ('notes', models.TextField(blank=True, default='')),
                ('accommodation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='pretalx_hitalx.accommodation')),
                ('speaker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accommodation_bookings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['from_date'],
            },
        ),
    ]
