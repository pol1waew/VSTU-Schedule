from api.utilities import WriteAPI, ReadAPI

from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected
from django.forms import BaseInlineFormSet
from django.utils import timezone

from api.models import (
    AbstractEvent,
    AbstractDay,
    ScheduleTemplateMetadata,
    ScheduleMetadata,
    ScheduleTemplate,
    Schedule,
    Department,
    Organization,
    Event,
    EventKind,
    EventParticipant,
    EventPlace,
    Subject,
    TimeSlot,
    DayDateOverride,
    EventCancel,
)

from rest_framework.authtoken.admin import TokenAdmin


class BaseAdmin(admin.ModelAdmin):
    readonly_fields = ("dateaccessed", "datemodified", "datecreated")

    def save_model(self, request, obj, form, change):
        if not obj.id:  # Если это новая запись
            obj.datecreated = timezone.now()
        obj.datemodified = timezone.now()
        obj.save()


@admin.register(Subject)
class SubjectAdmin(BaseAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(EventParticipant)
class EventParticipantAdmin(BaseAdmin):
    list_display = ("name", "role")
    search_fields = ("name", "role")
    list_filter = ("role",)


@admin.register(EventPlace)
class EventPlaceAdmin(BaseAdmin):
    list_display = ("building", "room")
    search_fields = ("building", "room")
    list_filter = ("building",)


@admin.register(EventKind)
class EventKindAdmin(BaseAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(ScheduleTemplateMetadata)
class ScheduleTemplateMetadataAdmin(BaseAdmin):
    list_display = ("faculty", "scope")
    search_fields = ("faculty", "scope")
    list_filter = ("faculty", "scope")


@admin.register(ScheduleMetadata)
class ScheduleMetadataAdmin(BaseAdmin):
    list_display = ("years", "course", "semester")
    search_fields = ("years", "course", "semester")
    list_filter = ("years", "course", "semester")


@admin.register(ScheduleTemplate)
class ScheduleTemplateAdmin(BaseAdmin):
    list_display = ("repetition_period", "department_name", "aligned_by_week_day")
    search_fields = ("repetition_period", "department__name", "aligned_by_week_day")
    list_filter = ("metadata__faculty", "metadata__scope")

    @admin.display(description=ScheduleTemplate._meta.get_field("department").verbose_name, 
                   ordering="department__name")
    def department_name(self, obj):
        return obj.department.name


@admin.register(Schedule)
class ScheduleAdmin(BaseAdmin):
    list_display = ("faculty", "course", "semester", "years")
    search_fields = ("schedule_template__metadata__faculty", "schedule_template__metadata__scope")
    list_filter = ("schedule_template__metadata__faculty", "schedule_template__metadata__scope", "metadata__course", "metadata__semester", "metadata__years")

    @admin.display(description=Schedule._meta.get_field("schedule_template").verbose_name, 
                   ordering="schedule_template__metadata__faculty")
    def faculty(self, obj):
        return obj.schedule_template.metadata.faculty

    @admin.display(description=ScheduleMetadata._meta.get_field("course").verbose_name, 
                   ordering="metadata__course")
    def course(self, obj):
        return obj.metadata.course

    @admin.display(description=ScheduleMetadata._meta.get_field("semester").verbose_name, 
                   ordering="metadata__semester")
    def semester(self, obj):
        return obj.metadata.semester

    @admin.display(description=ScheduleMetadata._meta.get_field("years").verbose_name, 
                   ordering="metadata__years")
    def years(self, obj):
        return obj.metadata.years


@admin.register(Event)
class EventAdmin(BaseAdmin):
    list_display = ("subject_override", "kind_override", "date", "time_slot_override")
    search_fields = ("subject_override", "date", "kind_override")
    list_filter = ("kind_override", "is_event_canceled")


@admin.register(AbstractEvent)
class AbstractEventAdmin(BaseAdmin):
    list_display = ("datemodified", "subject", "kind", "time_slot")
    search_fields = ("subject__name", "kind__name")
    list_filter = ("kind__name",)

    actions = ["delete_events", "fill"]

    @admin.action(description="Удалить связанные события")
    def delete_events(modeladmin, request, queryset):
        Event.objects.filter(abstract_event__in=queryset).delete()
        messages.success(request, "Связанные события успешно удалены")

    @admin.action(description="Заполнить семестр")
    def fill(modeladmin, request, queryset):
        if WriteAPI.fill_event_table(queryset):
            messages.success(request, "Успешно заполнено")
        else:
            messages.error(request, "Произошла ошибка")


@admin.register(AbstractDay)
class AbstractDayAdmin(BaseAdmin):
    list_display = ("name", "day_number")
    search_fields = ("name", "day_number")


@admin.register(Department)
class DepartmentAdmin(BaseAdmin):
    list_display = ("name", "organization_name")
    search_fields = ("name", "organization__name")
    list_filter = ("name", "organization__name")

    @admin.display(description=Department._meta.get_field("organization").verbose_name, 
                   ordering="organization__name")
    def organization_name(self, obj):
        return obj.organization.name


@admin.register(Organization)
class OrganizationAdmin(BaseAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    list_filter = ("name",)


@admin.register(TimeSlot)
class TimeSlotAdmin(BaseAdmin):
    list_display = ("alt_name", "start_time", "end_time")
    search_fields = ("alt_name", "start_time", "end_time")
    list_filter = ("alt_name",)


@admin.register(DayDateOverride)
class DayDateOverrideAdmin(BaseAdmin):
    list_display = ("day_source", "day_destination")
    search_fields = ("day_source", "day_destination")

    actions = ["override"]

    @admin.action(description="Применить переносы")
    def override(modeladmin, request, queryset):
        import api.utility_filters as filters

        for ddo in queryset:
            reader = ReadAPI(filters.DateFilter.from_singe_date(ddo.day_source))
            reader.add_filter(filters.EventFilter.by_department(ddo.department))
            
            reader.find_models(Event)
            
            for e in reader.get_found_models():
                WriteAPI.override_event_date(ddo, e)

        messages.success(request, "Успешно перенесены")


@admin.register(EventCancel)
class EventCancelAdmin(BaseAdmin):
    list_display = ("date", "department")
    search_fields = ("date", "department")


TokenAdmin.raw_id_fields = ["user"]