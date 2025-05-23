# Generated by Django 5.2.dev20241016095222 on 2025-05-19 18:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0028_rename_final_participants_abstracteventchanges_final_teachers_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='abstractevent',
            name='changes',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.abstracteventchanges', verbose_name='Изменения'),
        ),
        migrations.AlterField(
            model_name='abstracteventchanges',
            name='date_time',
            field=models.TextField(default='', null=True, verbose_name='Дата и учебный час'),
        ),
        migrations.AlterField(
            model_name='abstracteventchanges',
            name='final_date_time',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Дата и учебный час после изменений'),
        ),
        migrations.AlterField(
            model_name='abstracteventchanges',
            name='final_holds_on_date',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Заданный день после изменений'),
        ),
        migrations.AlterField(
            model_name='abstracteventchanges',
            name='final_places',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Места после изменений'),
        ),
        migrations.AlterField(
            model_name='abstracteventchanges',
            name='final_teachers',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Участники после изменений'),
        ),
        migrations.AlterField(
            model_name='abstracteventchanges',
            name='origin_holds_on_date',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Изначальные заданный день'),
        ),
        migrations.AlterField(
            model_name='event',
            name='abstract_event',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.abstractevent', verbose_name='Абстрактное событие'),
        ),
    ]
