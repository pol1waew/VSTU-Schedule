# Generated by Django 5.2.dev20241016095222 on 2025-02-12 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_alter_department_parent_department'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='participants_override',
            field=models.ManyToManyField(to='api.eventparticipant', verbose_name='Участники'),
        ),
    ]
