from typing import Optional, Self

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class CommonModel(models.Model):
    class Meta:
        abstract = True

    idnumber = models.CharField(
        unique=True,
        blank=True,
        null=True,
        max_length=260,
        verbose_name="Уникальный строковый идентификатор",
    )
    datecreated = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания записи")
    datemodified = models.DateTimeField(auto_now_add=True, verbose_name="Дата изменения записи")
    dateaccessed = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата доступа к записи"
    )
    author = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="Автор записи"
    )
    note = models.TextField(
        null=True, blank=True, verbose_name="Комментарий для этой записи", max_length=1024
    )

    @classmethod
    def last_modified_record(cls) -> Optional[Self]:
        return cls.objects.order_by("-datemodified").first()

    def __str__(self):
        return self.__repr__()


class Subject(CommonModel):
    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"

    name = models.CharField(max_length=256, verbose_name="Название")

    def __repr__(self):
        return "{} [{}]".format(str(self.name), self.pk)


class TimeSlot(CommonModel):
    class Meta:
        verbose_name = "Время проведения события"
        verbose_name_plural = "Времена проведения события"

    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(null=True, verbose_name="Время окончания")

    def clean(self):
        if self.end_time and self.end_time <= self.start_time:
            raise ValidationError("Время проведения не корректно")

    def __repr__(self):
        res = self.start_time.strftime("%H:%M")
        if self.end_time:
            res += "- {}".format(self.end_time.strftime("%H:%M"))
        return res


class EventPlace(CommonModel):
    class Meta:
        verbose_name = "Место проведения события"
        verbose_name_plural = "Места проведения события"

    building = models.CharField(max_length=128, verbose_name="Корпус")
    room = models.CharField(max_length=64, verbose_name="Аудитория")

    def __repr__(self):
        return str(self.room)


class EventParticipant(CommonModel):
    class Meta:
        verbose_name = "Участник события"
        verbose_name_plural = "Участники события"

    class Role(models.TextChoices):
        STUDENT = "student", "Студент"
        TEACHER = "teacher", "Преподаватель"
        ASSISTANT = "assistant", "Ассистент"

    name = models.CharField(max_length=255, verbose_name="Имя")
    role = models.CharField(choices=Role, max_length=48, null=False, verbose_name="Роль")

    def __repr__(self):
        return str(self.name) + f" ({self.role})"


class EventKind(CommonModel):
    class Meta:
        verbose_name = "Тип события"
        verbose_name_plural = "Типы событий"

    name = models.CharField(verbose_name="Название типа", max_length=64)

    def __repr__(self):
        return "{} [{}]".format(str(self.name), self.pk)


class Schedule(CommonModel):
    class Meta:
        verbose_name = "Расписание"
        verbose_name_plural = "Расписания"

    class Scope(models.TextChoices):
        BACHELOR = "bachelor", "Бакалавриат"
        MASTER = "master", "Магистратура"
        POSTGRADUATE = "postgraduate", "Аспирантура"
        CONSULTATION = "consultation", "Консультация"

    faculty = models.CharField(max_length=32, verbose_name="Факультет")
    scope = models.CharField(choices=Scope, max_length=32, verbose_name="Обучение")
    course = models.IntegerField(verbose_name="Курс")
    semester = models.IntegerField(verbose_name="Семестр")
    years = models.CharField(max_length=16, verbose_name="Учебный год")

    def first_event(self):
        events = self.events.all()

        return events.annotate(min_date=models.Min("holdings__date")).order_by("min_date").first()

    def last_event(self):
        events = self.events.all()

        return events.annotate(max_date=models.Max("holdings__date")).order_by("-max_date").first()

    def __repr__(self):
        return f"{self.faculty},{self.years},{self.scope},{self.course}к,{self.semester}сем"


class Event(CommonModel):
    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"

    kind = models.ForeignKey(EventKind, on_delete=models.PROTECT, verbose_name="Тип")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, verbose_name="Предмет")
    participants = models.ManyToManyField(EventParticipant, verbose_name="Участники")
    schedule = models.ForeignKey(
        Schedule,
        verbose_name="Связанное расписание",
        related_name="events",
        on_delete=models.CASCADE,
    )

    def __repr__(self):
        return f"Занятие по {self.subject.name} [{self.pk}]"


class EventHolding(CommonModel):
    class Meta:
        verbose_name = "Информация о проведении события"
        verbose_name_plural = verbose_name

    place = models.ForeignKey(EventPlace, on_delete=models.PROTECT, verbose_name="Место")
    date = models.DateField(blank=False, verbose_name="Дата")
    time_slot = models.ForeignKey(
        TimeSlot, on_delete=models.PROTECT, verbose_name="Временной интервал"
    )
    event = models.ForeignKey(
        Event,
        null=True,
        on_delete=models.SET_NULL,
        related_name="holdings",
        verbose_name="Связанное событие",
    )

    def __repr__(self):
        return f"{self.place}, {self.date.strftime('%Y-%m-%d')}, {self.time_slot}"
