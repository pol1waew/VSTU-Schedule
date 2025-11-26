from typing import Optional, Self
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save, post_save, pre_delete, m2m_changed
from django.dispatch import receiver
from django.urls import reverse


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
        return str(self.name)


class TimeSlot(CommonModel):
    class Meta:
        verbose_name = "Время проведения события"
        verbose_name_plural = "Времена проведения события"

    alt_name = models.TextField(blank=True, null=True, verbose_name="Академ. часы пары")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(blank=True, null=True, verbose_name="Время окончания")

    def clean(self):
        if self.end_time and self.end_time <= self.start_time:
            raise ValidationError("Время проведения не корректно")

    def __repr__(self):
        res = self.start_time.strftime("%H:%M").removeprefix("0")

        if self.end_time:
            res += "-{}".format(self.end_time.strftime("%H:%M"))
        
        if self.alt_name:
            return f"{self.alt_name}ч. / {res}"
        else:
            return f"{res}"


class EventPlace(CommonModel):
    class Meta:
        verbose_name = "Место проведения события"
        verbose_name_plural = "Места проведения события"

    building = models.CharField(blank=True, default="", db_default="", max_length=128, verbose_name="Корпус")
    room = models.CharField(max_length=64, verbose_name="Аудитория")

    def __repr__(self):
        return f"{self.building} {self.room}"
    
    def get_absolute_url(self):
        return reverse("admin:api_eventplace_change", args=[self.pk])


class EventKind(CommonModel):
    class Meta:
        verbose_name = "Тип события"
        verbose_name_plural = "Типы событий"

    name = models.CharField(verbose_name="Название типа", max_length=64)

    def __repr__(self):
        return str(self.name)


class AbstractDay(CommonModel):
    class Meta:
        verbose_name = "Абстрактный день"
        verbose_name_plural = "Абстрактные дни"

    day_number = models.IntegerField(verbose_name="Смещение от начала повторяющгося фрагмента (пн. первой недели)")
    name = models.CharField(verbose_name="Имя дня в рамках шаблона", max_length=64)

    def __repr__(self):
        return f"{str(self.name)}"


class Organization(CommonModel):
    class Meta:
        verbose_name = "Учреждение"
        verbose_name_plural = "Учреждения"

    name = models.CharField(verbose_name="Имя учреждения", max_length=64)

    def __repr__(self):
        return str(self.name)


class Department(CommonModel):
    class Meta:
        verbose_name = "Подразделение"
        verbose_name_plural = "Подразделения"

    name = models.CharField(verbose_name="Имя подразделения", max_length=64)
    shortname = models.CharField(blank=True, null=True, verbose_name="Аббревиатура", max_length=16)
    code = models.CharField(verbose_name="Код подразделения", max_length=16)
    parent_department = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Родительское подразделение"
        )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name="Учреждение")

    def __repr__(self):
        return str(self.name)


class ScheduleTemplateMetadata(CommonModel):
    class Meta:
        verbose_name = "Метаданные шаблона расписания"
        verbose_name_plural = "Метаданные шаблона расписания"

    class Scope(models.TextChoices):
        BACHELOR = "bachelor", "Бакалавриат"
        MASTER = "master", "Магистратура"
        POSTGRADUATE = "postgraduate", "Аспирантура"
        CONSULTATION = "consultation", "Консультация"

    faculty = models.CharField(max_length=32, verbose_name="Факультет")
    scope = models.CharField(choices=Scope, max_length=32, verbose_name="Обучение")

    def __repr__(self):
        return f"{self.faculty}, {self.scope}"


class ScheduleMetadata(CommonModel):
    class Meta:
        verbose_name = "Метаданные расписания"
        verbose_name_plural = "Метаданные расписания"

    years = models.CharField(max_length=16, verbose_name="Учебный год")
    course = models.IntegerField(verbose_name="Курс")
    semester = models.IntegerField(verbose_name="Семестр")
    
    def __repr__(self):
        return f"{self.years}, {self.course}курс, {self.semester}сем"


class ScheduleTemplate(CommonModel):
    class Meta:
        verbose_name = "Шаблон расписания"
        verbose_name_plural = "Шаблоны расписаний"

    metadata = models.ForeignKey(ScheduleTemplateMetadata, null=True, on_delete=models.PROTECT, verbose_name="Факультет, обучение")
    repetition_period = models.IntegerField(verbose_name="Период повторения в днях")
    repeatable = models.BooleanField(verbose_name="Повторяется ли")
    aligned_by_week_day = models.IntegerField(verbose_name="Выравнивание относительно дня недели (null=0, пн=1, ...)")
    department = models.ForeignKey(Department, null=True, on_delete=models.SET_NULL, verbose_name="Подразделение")

    def __repr__(self):
        if self.repetition_period in [0, 5, 6, 7, 8, 9] or self.repetition_period // 10 == 1:
            return f"{self.department}, каждые {self.repetition_period} дней"
        
        if self.repetition_period % 10 == 1:
            return f"{self.department}, каждый {self.repetition_period} день"
        
        if self.repetition_period % 10 in [2, 3, 4]:
            return f"{self.department}, каждые {self.repetition_period} дня"
        
        return f"{self.department}"
    
    def save(self, **kwargs):
        super().save(**kwargs)

        from api.utilities import WriteAPI, ReadAPI
        import api.utility_filters as filters

        reader = ReadAPI({"schedule__schedule_template" : self})
        # getting AbstractEvents with existing Events
        reader.add_filter(filters.AbstractEventFilter.with_existing_events())
        
        reader.find_models(AbstractEvent)

        WriteAPI.fill_event_table(reader.get_found_models())


class Schedule(CommonModel):
    class Meta:
        verbose_name = "Расписание"
        verbose_name_plural = "Расписания"

    class Status(models.IntegerChoices):
        ACTIVE = 0, "Активно"
        DISABLED = 1, "Отключено"
        FUTURE = 2, "Будущее"
        ARCHIVE = 3, "Архивное"

    metadata = models.ForeignKey(ScheduleMetadata, null=True, on_delete=models.PROTECT, verbose_name="Курс, семестр, год")
    status = models.IntegerField(choices=Status, default=0, verbose_name="Текущий статус")
    start_date = models.DateField(null=True, verbose_name="День начала семестра (вкл.)")
    end_date = models.DateField(null=True, verbose_name="День окончания семестра (вкл.)")
    starting_day_number = models.ForeignKey(AbstractDay, null=True, on_delete=models.PROTECT, verbose_name="Номер дня начала первого повторяющегося цикла") 
    schedule_template = models.ForeignKey(ScheduleTemplate, null=True, on_delete=models.PROTECT, verbose_name="Шаблон расписания")

    def first_event(self):
        events = self.events.all()

        return events.annotate(min_date=models.Min("holdings__date")).order_by("min_date").first() ####

    def last_event(self):
        events = self.events.all()

        return events.annotate(max_date=models.Max("holdings__date")).order_by("-max_date").first()   ######

    def __repr__(self):
        return f"{self.schedule_template.metadata}, {self.metadata}"
    
    def save(self, **kwargs):
        super().save(**kwargs)
        
        from api.utilities import WriteAPI, ReadAPI
        import api.utility_filters as filters

        reader = ReadAPI({"schedule" : self})
        # getting AbstractEvent with existing Event
        reader.add_filter(filters.AbstractEventFilter.with_existing_events())
        
        reader.find_models(AbstractEvent)

        WriteAPI.fill_event_table(reader.get_found_models())


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
    is_group = models.BooleanField(verbose_name="Является группой", default=False)
    department = models.ForeignKey(Department, null=True, on_delete=models.SET_NULL, verbose_name="Подразделение")

    def __repr__(self):
        return f"{self.name} ({self.role})"
    
    def get_absolute_url(self):
        return reverse("admin:api_eventparticipant_change", args=[self.pk])


class AbstractEventChanges(CommonModel):
    class Meta:
        verbose_name = "Изменения в запланированном событии"
        verbose_name_plural = "Изменения в запланированных событиях"

    group = models.TextField(null=True, default="", verbose_name="Группа")
    date_time = models.TextField(null=True, default="", verbose_name="Дата и учебный час")
    subject = models.TextField(null=True, verbose_name="Занятие")
    is_created = models.BooleanField(verbose_name="Запланированное событие создано", default=False)
    is_deleted = models.BooleanField(verbose_name="Запланированное событие удалено", default=False)
    is_exported = models.BooleanField(verbose_name="Запланированное событие экспортировано", default=False)
    origin_teachers = models.TextField(null=True, blank=True, default="", verbose_name="Изначальные участники")
    origin_places = models.TextField(null=True, blank=True, default="", verbose_name="Изначальные места")
    origin_holds_on_date = models.TextField(null=True, blank=True, default="", verbose_name="Изначальные заданный день")
    origin_kind = models.TextField(null=True, blank=True, default="", verbose_name="Изначальный тип")
    final_teachers = models.TextField(null=True, blank=True, default="", verbose_name="Участники после изменений")
    final_places = models.TextField(null=True, blank=True, default="", verbose_name="Места после изменений")
    final_date_time = models.TextField(null=True, blank=True, default="", verbose_name="Дата и учебный час после изменений")
    final_holds_on_date = models.TextField(null=True, blank=True, default="", verbose_name="Заданный день после изменений")
    final_kind = models.TextField(null=True, blank=True, default="", verbose_name="Тип после изменений")

    def __repr__(self):
        return f"{self.group}, {self.date_time}, {self.subject}"
    
    def __str__(self):
        return f"{self.group}, {self.date_time}, {self.subject}"
    
    def save(self, **kwargs):
        super().save(**kwargs)

        # when logging AbsEvent deleting
        # no need to validate fields
        if self.is_deleted:
            return

        if self.final_teachers and self.origin_teachers == self.final_teachers:
            self.final_teachers = None

        if self.final_places and self.origin_places == self.final_places:
            self.final_places = None

        if self.final_date_time and self.date_time == self.final_date_time:
            self.final_date_time = None

        if self.final_holds_on_date and self.origin_holds_on_date == self.final_holds_on_date:
            self.final_holds_on_date = None

        if self.final_kind and self.origin_holds_on_date == self.final_kind:
            self.final_kind = None
    
    @staticmethod
    def str_from_participants(participants) -> str:
        """Makes formated str to store from given EventParticipant
        """

        return_value = ""

        for p in participants:
            return_value += f"{p.name}, "
        return_value = return_value[:-2]
        
        return return_value
    
    @staticmethod
    def str_from_places(places) -> str:
        """Makes formated str to store from given EventPlace
        """

        return_value = ""

        for p in places:
            return_value += f"{p}, "
        return_value = return_value[:-2]

        return return_value

    @staticmethod
    def str_from_date_time(abstract_event) -> str:
        """Makes formated str to store from given AbstractEvent's day and time_slot
        """
        
        return f"{abstract_event.abstract_day} / {abstract_event.time_slot.alt_name}ч."

    def initialize(self, ae):
        """Fills model with origin values from given AbstractEvent
        """
        
        self.group = self.str_from_participants(ae.get_groups())
        self.date_time = self.str_from_date_time(ae)
        self.subject = ae.subject.name
        self.origin_teachers = self.str_from_participants(ae.get_teachers())
        self.origin_places = self.str_from_places(ae.places.all())
        self.origin_holds_on_date = ae.holds_on_date
        self.origin_kind = ae.kind.name if ae.kind else ""

    def export(self) -> list[list[str]]:
        """Prepare stored data to export
        """
        
        export_data_base = [self.datemodified.strftime('%Y-%m-%d %H:%M:%S'), self.group, self.date_time, self.subject]
        export_data = []

        if self.is_deleted:
            export_data.append(export_data_base + ["УДАЛЕНО"])
        else:
            if self.is_created:
                export_data.append(export_data_base + ["СОЗДАНО"])

            if self.final_teachers:
                export_data.append(export_data_base + ["ПРЕПОДАВАТЕЛЬ", self.origin_teachers, self.final_teachers])

            if self.final_places:
                export_data.append(export_data_base + ["АУДИТОРИЯ", self.origin_places, self.final_places])
            
            if self.final_date_time:
                export_data.append(export_data_base + ["ДЕНЬ НЕДЕЛИ/УЧ. ЧАС", self.date_time, self.final_date_time])

            if self.final_holds_on_date:
                export_data.append(export_data_base + ["ЯВНАЯ ДАТА", self.origin_holds_on_date, self.final_holds_on_date])

            if self.final_kind:
                export_data.append(export_data_base + ["ТИП", self.origin_kind, self.final_kind])

        self.is_exported = True
        
        self.save()

        self.clear_relation_with_abs_event()

        return export_data
    
    def clear_relation_with_abs_event(self):
        """Removes all references to self from related AbstractEvents
        """
        
        for ae in AbstractEvent.objects.filter(changes=self):
            ae.changes = None

            ae.save()


class AbstractEvent(CommonModel):
    class Meta:
        verbose_name = "Запланированное событие"
        verbose_name_plural = "Запланированные события"

    kind = models.ForeignKey(EventKind, null=True, blank=True, default=None, on_delete=models.PROTECT, verbose_name="Тип")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, verbose_name="Предмет")
    participants = models.ManyToManyField(EventParticipant, verbose_name="Участники")
    places = models.ManyToManyField(EventPlace, verbose_name="Места")
    abstract_day = models.ForeignKey(AbstractDay, on_delete=models.PROTECT, verbose_name="Абстрактный день")
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.PROTECT, verbose_name="Временной интервал") # null=True, blank=True
    # for many dates should create many AbstractEvents
    holds_on_date = models.DateField(null=True, blank=True, verbose_name="Проводится только в заданный день")
    schedule = models.ForeignKey(Schedule, null=True, on_delete=models.CASCADE, related_name="events", verbose_name="Расписание")
    changes = models.ForeignKey(AbstractEventChanges, null=True, blank=True, on_delete=models.SET_NULL, editable=False, verbose_name="Изменения")

    def __repr__(self):
        return f"Занятие по {self.subject.name}, {self.time_slot.alt_name}ч."
    
    def save(self, **kwargs):
        super().save(**kwargs)

        from api.utilities import WriteAPI

        # calling here because need updated AbstractEvent reference inside Events
        WriteAPI.update_events(self, update_m2m=False)
    
    @property
    def department(self):
        """Returns Event Department
        """
        
        return self.schedule.schedule_template.department
    
    def get_groups(self):
        """Filter and returns groups from participants 
        """
        
        return self.participants.filter(is_group=True)
    
    def get_teachers(self):
        """Filter and returns teachers from participants 
        """

        return self.participants.filter(role__in=[EventParticipant.Role.TEACHER, EventParticipant.Role.ASSISTANT])
    
    def get_absolute_url(self):
        return reverse("admin:api_abstractevent_change", args=[self.pk])

    def generate_changes_on_creating(self):
        """Create AbstractEventChange model

        Should be called when AbstractEvent model creates

        Not saving self instance on complete
        """
        
        changes = AbstractEventChanges()
        
        changes.date_time = AbstractEventChanges.str_from_date_time(self)
        changes.subject = self.subject.name
        changes.is_created = True

        if self.holds_on_date:
            changes.final_holds_on_date = self.holds_on_date

        changes.final_kind = self.kind.name if self.kind else ""

        changes.save()

        self.changes = changes

    def update_change_model(self):
        """Writes AbsractEvent changes into AbstractEventChange model

        If no changes done do nothing. Looking for only non m2m fields

        Not saving self instance on complete
        """

        previous_ae = AbstractEvent.objects.get(pk=self.pk)

        is_date_time_changed = previous_ae.abstract_day != self.abstract_day or previous_ae.time_slot != self.time_slot
        is_holds_on_date_changed = previous_ae.holds_on_date != self.holds_on_date
        is_kind_changed = previous_ae.kind != self.kind

        # continue only if something changed
        if not is_date_time_changed and not is_holds_on_date_changed and not is_kind_changed:
            return
        
        changes = previous_ae.changes

        if not changes:
            changes = AbstractEventChanges()

            changes.initialize(previous_ae)

        if is_date_time_changed:
            changes.final_date_time = AbstractEventChanges.str_from_date_time(self)

        if is_holds_on_date_changed:
            changes.final_holds_on_date = self.holds_on_date

        if is_kind_changed:
            changes.final_kind = self.kind.name if self.kind else ""

        changes.save()

        self.changes = changes

@receiver(m2m_changed, sender=AbstractEvent.participants.through)
def participants_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Writes AbstractEvent participants changes and update related Events
    """

    if action == "pre_add" or action == "pre_remove":
        if not instance.changes:
            changes = AbstractEventChanges()

            changes.initialize(instance)

            changes.save()

            instance.changes = changes

            instance.save()
    elif action == "post_add" or action == "post_remove":
        from api.utilities import WriteAPI

        WriteAPI.update_events(instance, update_non_m2m=False)

        instance.changes.group = AbstractEventChanges.str_from_participants(instance.get_groups())
        instance.changes.final_teachers = AbstractEventChanges.str_from_participants(instance.get_teachers())

        instance.changes.save()

@receiver(m2m_changed, sender=AbstractEvent.places.through)
def places_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Writes AbstractEvent places changes and update related Events
    """

    if action == "pre_add" or action == "pre_remove":
        if not instance.changes:
            changes = AbstractEventChanges()

            changes.initialize(instance)

            changes.save()

            instance.changes = changes

            instance.save()
    elif action == "post_add" or action == "post_remove":
        from api.utilities import WriteAPI

        WriteAPI.update_events(instance, update_non_m2m=False)
        
        instance.changes.final_places = AbstractEventChanges.str_from_places(instance.places.all())

        instance.changes.save()

@receiver(pre_save, sender=AbstractEvent)
def on_abstract_event_pre_save(sender, instance, **kwargs):
    # AbsEvent created
    if instance.pk is None:
        instance.generate_changes_on_creating()

        return

    instance.update_change_model()

    if AbstractEvent.objects.get(pk=instance.pk).abstract_day != instance.abstract_day:
        from api.utilities import WriteAPI

        WriteAPI.fill_event_table(instance)

@receiver(pre_delete, sender=AbstractEvent)
def on_abstract_event_delete(sender, instance, **kwargs): 
    if instance.changes and instance.changes.is_created and not instance.changes.is_exported:
        instance.changes.delete()
        
        return

    changes = AbstractEventChanges()

    changes.initialize(instance)

    changes.is_deleted = True

    changes.save()
            

class EventCancel(CommonModel):
    class Meta:
        verbose_name = "Отмена событий"
        verbose_name_plural = "Отмены событий"

    date = models.DateField(blank=False, verbose_name="Отменить для даты")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="Подразделение")

    def __repr__(self):
        return f"Отмена событий на {self.date}"    
    
    def save(self, **kwargs):
        super().save(**kwargs)
        
        from api.utilities import WriteAPI, ReadAPI
        import api.utility_filters as filters

        reader = ReadAPI(filters.DateFilter.from_singe_date(self.date))
        reader.add_filter(filters.EventFilter.by_department(self.department))
        
        reader.find_models(Event)
        
        for e in reader.get_found_models():
            WriteAPI.apply_event_canceling(self, e)

@receiver(pre_save, sender=EventCancel)
def on_event_cancel_date_override(sender, instance, **kwargs):
    created = instance.pk is None

    if created:
        return
    
    previous_cancel = EventCancel.objects.get(pk=instance.pk)

    # if EventCancel moved to other date
    # need to undo Events canceling
    if previous_cancel.date != instance.date:
        from api.utilities import WriteAPI, ReadAPI

        reader = ReadAPI({"event_cancel" : previous_cancel})
        
        reader.find_models(Event)
        
        for e in reader.get_found_models():
            WriteAPI.apply_event_canceling(None, e)

@receiver(pre_delete, sender=EventCancel)
def on_event_cancel_delete(sender, instance, **kwargs):
    from api.utilities import WriteAPI, ReadAPI

    reader = ReadAPI({"event_cancel" : instance})
    
    reader.find_models(Event)
    
    for e in reader.get_found_models():
        WriteAPI.apply_event_canceling(None, e)


class DayDateOverride(CommonModel):
    class Meta:
        verbose_name = "Перенос дня на другую дату"
        verbose_name_plural = "Переносы дней на другие даты"

    day_source = models.DateField(blank=False, verbose_name="Перенести с даты")
    day_destination = models.DateField(blank=False, verbose_name="Перенести на дату")
    department = models.ForeignKey(Department, null=True, on_delete=models.CASCADE, verbose_name="Подразделение")

    def __repr__(self):
        return f"Перенос с {self.day_source} на {self.day_destination}"
    
    def save(self, **kwargs):
        super().save(**kwargs)

        from api.utilities import WriteAPI, ReadAPI
        import api.utility_filters as filters

        reader = ReadAPI(filters.DateFilter.from_singe_date(self.day_source))
        reader.add_filter(filters.EventFilter.by_department(self.department))
        
        reader.find_models(Event)
        
        for e in reader.get_found_models():
            WriteAPI.apply_date_override(self, e)

@receiver(pre_save, sender=DayDateOverride)
def on_date_override_source_override(sender, instance, **kwargs):
    created = instance.pk is None

    if created:
        return
    
    previous_override = DayDateOverride.objects.get(pk=instance.pk)

    # if DayDateOverride moved to other date
    # need to detach it from Events
    if previous_override.day_source != instance.day_source:
        from api.utilities import WriteAPI, ReadAPI

        reader = ReadAPI({"date_override" : previous_override})
        
        reader.find_models(Event)

        for e in reader.get_found_models():
            WriteAPI.apply_date_override(None, e)

@receiver(pre_delete, sender=DayDateOverride)
def on_day_date_override_delete(sender, instance, **kwargs):
    from api.utilities import WriteAPI, ReadAPI

    reader = ReadAPI({"date_override" : instance})
        
    reader.find_models(Event)
    
    for e in reader.get_found_models():
            WriteAPI.apply_date_override(None, e)


class Event(CommonModel):
    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"

    date = models.DateField(null=True, blank=False, verbose_name="Дата")
    date_override = models.ForeignKey(DayDateOverride, null=True, blank=True, editable=False, on_delete=models.SET_NULL, verbose_name="Перенос дня")
    kind_override = models.ForeignKey(EventKind, null=True, blank=True, default=None, on_delete=models.PROTECT, verbose_name="Тип")
    subject_override = models.ForeignKey(Subject, null=True, on_delete=models.PROTECT, verbose_name="Предмет")
    participants_override = models.ManyToManyField(EventParticipant, verbose_name="Участники")
    places_override = models.ManyToManyField(EventPlace, verbose_name="Места")
    time_slot_override = models.ForeignKey(TimeSlot, null=True, on_delete=models.PROTECT, verbose_name="Временной интервал")
    abstract_event = models.ForeignKey(AbstractEvent, null=True, editable=False, on_delete=models.CASCADE, verbose_name="Запланированное событие")
    is_event_canceled = models.BooleanField(verbose_name="Событие отменено", default=False)
    event_cancel = models.ForeignKey(EventCancel, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Отмена события")
    is_event_overriden = models.BooleanField(verbose_name="Событие изменено вручную", default=False)

    @property
    def department(self):
        return self.abstract_event.schedule.schedule_template.department
    
    def get_groups(self):
        return self.participants_override.filter(is_group=True)
    
    def get_teachers(self):
        return self.participants_override.filter(role__in=[EventParticipant.Role.TEACHER, EventParticipant.Role.ASSISTANT])

    def __repr__(self):
        return f"Занятие по {self.abstract_event.subject.name}"    

    def check_date_interactions(self):
        """Checks Event date and attaching/detaching DayDateOverride if needed
        """

        if not self.date_override:
            from api.utilities import WriteAPI, ReadAPI

            reader = ReadAPI({"day_source" : self.date})
            reader.add_filter({"department" : self.department})

            reader.find_models(DayDateOverride)

            if reader.get_found_models().exists():
                WriteAPI.apply_date_override(reader.get_found_models().first(), self, call_save_method=False)

            return

        # if destination date from attached DayDateOverride
        # differ from Event date
        if self.date_override.day_destination != self.date:
            # need detach DayDateOverride from Event
            self.date_override = None

    def check_canceling(self):
        """Checks Event date and attaching/detaching EventCancel if needed
        """

        # skip manualy canceled events
        if self.is_event_canceled and not self.event_cancel:
            return

        from api.utilities import WriteAPI, ReadAPI
        import api.utility_filters as filters

        reader = ReadAPI({"department" : self.department})
        reader.add_filter(filters.DateFilter.from_singe_date(self.date))

        reader.find_models(EventCancel)

        if reader.get_found_models().exists():
            WriteAPI.apply_event_canceling(reader.get_found_models().first(), self, False)
        else:
            self.is_event_canceled = False
            self.event_cancel = None
        

@receiver(m2m_changed, sender=Event.participants_override.through)
def participants_override_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == "post_add" or action == "post_remove":
        if not instance.is_event_overriden and list(instance.participants_override.all()) != list(instance.abstract_event.participants.all()):
            instance.is_event_overriden = True

            instance.save()

@receiver(m2m_changed, sender=Event.places_override.through)
def places_override_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == "post_add" or action == "post_remove":
        if not instance.is_event_overriden and list(instance.places_override.all()) != list(instance.abstract_event.places.all()):
            instance.is_event_overriden = True

            instance.save()

@receiver(pre_save, sender=Event)
def on_event_save(sender, instance, **kwargs):
    created = instance.pk is None
    previous_event = None

    if not created:
        previous_event = Event.objects.get(pk=instance.pk)

        # check for override by non m2m fields
        if not instance.is_event_overriden:
            if instance.kind_override != instance.abstract_event.kind or \
                instance.subject_override != instance.abstract_event.subject or \
                instance.time_slot_override != instance.abstract_event.time_slot or \
                instance.is_event_canceled and not instance.event_cancel:
                instance.is_event_overriden = True

    instance.check_date_interactions()
            
    # if Event was created or date changed
    # need to check for event canceling
    if created or previous_event.date != instance.date:
        instance.check_canceling()
        
    # if EventCancel was manualy setted in Event
    # but is_event_canceled not checked
    # make Event canceled
    if not created and not instance.is_event_canceled and not previous_event.event_cancel and instance.event_cancel:
        instance.is_event_canceled = True
