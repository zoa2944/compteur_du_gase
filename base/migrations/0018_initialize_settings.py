# Generated by Django 3.1.2 on 2020-10-04 23:31

from django.db import migrations


def initialize_settings_if_needed(apps, schema_editor):
    LocalSettings = apps.get_model('base', 'localsettings')
    if not LocalSettings.objects.exists():
        LocalSettings.objects.create()


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0017_auto_20201004_2353'),
    ]

    operations = [
        migrations.RunPython(
            initialize_settings_if_needed,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
