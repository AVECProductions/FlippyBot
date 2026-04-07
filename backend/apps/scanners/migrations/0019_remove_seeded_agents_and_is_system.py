from django.db import migrations


def delete_seeded_agents(apps, schema_editor):
    """Remove the original three hardcoded/seeded agents."""
    Agent = apps.get_model('scanners', 'Agent')
    Agent.objects.filter(slug__in=['skis', 'vehicles', 'dj_equipment']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('scanners', '0018_allow_blank_icon'),
    ]

    operations = [
        migrations.RunPython(delete_seeded_agents, migrations.RunPython.noop),
    ]
