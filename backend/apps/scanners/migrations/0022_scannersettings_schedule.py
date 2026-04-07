import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scanners', '0021_worker_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='scannersettings',
            name='schedule_enabled',
            field=models.BooleanField(default=False, help_text='Only run scans within the configured time window'),
        ),
        migrations.AddField(
            model_name='scannersettings',
            name='schedule_start',
            field=models.TimeField(default=datetime.time(6, 30), help_text='Window open time (America/Denver / MST)'),
        ),
        migrations.AddField(
            model_name='scannersettings',
            name='schedule_end',
            field=models.TimeField(default=datetime.time(23, 0), help_text='Window close time (America/Denver / MST)'),
        ),
        migrations.AddField(
            model_name='scannersettings',
            name='schedule_timezone',
            field=models.CharField(default='America/Denver', help_text='Timezone for schedule window', max_length=50),
        ),
    ]
