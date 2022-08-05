# Generated by Django 4.0.6 on 2022-08-05 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dcim', '0182_remove_device_software_program'),
    ]

    operations = [
        migrations.AlterField(
            model_name='program',
            name='device',
            field=models.ManyToManyField(blank=True, related_name='programs', to='dcim.device'),
        ),
        migrations.AlterField(
            model_name='program',
            name='id',
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
    ]
