"""
Data migration: reset schedule window to correct defaults on any existing
ScannerSettings row. Runs automatically on Railway deploy.

Correct defaults:
  schedule_start = 06:30  (window opens 6:30 AM MST)
  schedule_end   = 23:00  (window closes 11:00 PM MST)
  schedule_enabled = False (off by default — user must opt in)
"""
import datetime
from django.db import migrations


def reset_schedule(apps, schema_editor):
    ScannerSettings = apps.get_model('scanners', 'ScannerSettings')
    ScannerSettings.objects.filter(id=1).update(
        schedule_start=datetime.time(6, 30),
        schedule_end=datetime.time(23, 0),
        schedule_enabled=False,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('scanners', '0022_scannersettings_schedule'),
    ]

    operations = [
        migrations.RunPython(reset_schedule, migrations.RunPython.noop),
    ]
