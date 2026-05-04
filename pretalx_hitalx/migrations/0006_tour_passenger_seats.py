from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pretalx_hitalax', '0005_accommodation'),
    ]

    operations = [
        # 1. Create the explicit through model (new table with seats column)
        migrations.CreateModel(
            name='TourPassenger',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seats', models.PositiveSmallIntegerField(default=1)),
                ('tour', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tour_passengers',
                    to='pretalx_hitalax.tour',
                )),
                ('speaker', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tour_passengers',
                    to='person.speakerprofile',
                )),
            ],
            options={
                'unique_together': {('tour', 'speaker')},
            },
        ),
        # 2. Copy existing M2M data into the new through table (seats defaults to 1)
        migrations.RunSQL(
            sql="""
                INSERT INTO pretalx_hitalax_tourpassenger (tour_id, speaker_id, seats)
                SELECT tour_id, speakerprofile_id, 1
                FROM pretalx_hitalax_tour_passengers
                ON CONFLICT DO NOTHING
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 3. Update Django's internal state: Tour.passengers now uses the through model
        migrations.AlterField(
            model_name='tour',
            name='passengers',
            field=models.ManyToManyField(
                through='pretalx_hitalax.TourPassenger',
                related_name='tours',
                to='person.speakerprofile',
            ),
        ),
        # 4. Drop the old implicit M2M table (no longer needed)
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS pretalx_hitalax_tour_passengers',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
