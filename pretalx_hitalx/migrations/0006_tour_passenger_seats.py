from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pretalx_hitalx', '0005_accommodation'),
    ]

    operations = [
        # 1. Create the explicit through model table
        migrations.CreateModel(
            name='TourPassenger',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seats', models.PositiveSmallIntegerField(default=1)),
                ('tour', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tour_passengers',
                    to='pretalx_hitalx.tour',
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
        # 2. Copy existing M2M rows into the new through table (seats=1 for all)
        migrations.RunSQL(
            sql="""
                INSERT INTO pretalx_hitalx_tourpassenger (tour_id, speaker_id, seats)
                SELECT tour_id, speakerprofile_id, 1
                FROM pretalx_hitalx_tour_passengers
                ON CONFLICT DO NOTHING
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 3. Remove the old implicit M2M field (drops pretalx_hitalx_tour_passengers table)
        migrations.RemoveField(
            model_name='tour',
            name='passengers',
        ),
        # 4. Add back the M2M field pointing at the through model.
        #    State-only: the through table already exists from step 1.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='tour',
                    name='passengers',
                    field=models.ManyToManyField(
                        through='pretalx_hitalx.TourPassenger',
                        related_name='tours',
                        to='person.speakerprofile',
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
