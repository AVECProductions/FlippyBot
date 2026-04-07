from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scanners', '0019_remove_seeded_agents_and_is_system'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='agent',
            name='is_system',
        ),
    ]
