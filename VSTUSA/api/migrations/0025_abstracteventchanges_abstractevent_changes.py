# Generated by Django 5.2.dev20241016095222 on 2025-05-19 10:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0024_alter_event_date_override'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AbstractEventChanges',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idnumber', models.CharField(blank=True, max_length=260, null=True, unique=True, verbose_name='Уникальный строковый идентификатор')),
                ('datecreated', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания записи')),
                ('datemodified', models.DateTimeField(auto_now_add=True, verbose_name='Дата изменения записи')),
                ('dateaccessed', models.DateTimeField(blank=True, null=True, verbose_name='Дата доступа к записи')),
                ('note', models.TextField(blank=True, max_length=1024, null=True, verbose_name='Комментарий для этой записи')),
                ('origin_participants', models.TextField(null=True, verbose_name='Изначальные участники')),
                ('final_participants', models.TextField(null=True, verbose_name='Участники после изменений')),
                ('origin_places', models.TextField(null=True, verbose_name='Изначальные места')),
                ('final_places', models.TextField(null=True, verbose_name='Места после изменений')),
                ('origin_date_time', models.TextField(null=True, verbose_name='Изначальная дата и учебный час')),
                ('final_date_time', models.TextField(null=True, verbose_name='Дата и учебный час после изменений')),
                ('origin_holds_on_date', models.TextField(null=True, verbose_name='Изначальные заданный день')),
                ('final_holds_on_date', models.TextField(null=True, verbose_name='Заданный день после изменений')),
                ('is_created', models.BooleanField(default=False, verbose_name='Создано')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='Удалено')),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Автор записи')),
            ],
            options={
                'verbose_name': 'Изменения в абстрактном событии',
                'verbose_name_plural': 'Изменения в абстрактных событиях',
            },
        ),
        migrations.AddField(
            model_name='abstractevent',
            name='changes',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='api.abstracteventchanges', verbose_name='Изменения'),
        ),
    ]
