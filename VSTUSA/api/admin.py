from api.utilities import Utilities, ReadAPI, WriteAPI
import api.utility_filters as filters
from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected
from django.forms import BaseInlineFormSet
from django.utils import timezone
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from rest_framework.authtoken.admin import TokenAdmin
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
    AbstractEventChanges
)


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
    class EventOverridenFilter(admin.SimpleListFilter):
        title = "Событие перезаписано"
        parameter_name = "is_overriden"
        OVERRIDEN_NAMES = ("Перезаписан", "Перезаписаны")
        NOT_OVERRIDEN_NAMES = ("Не перезаписан", "Не перезаписаны")

        def lookups(self, request, model_admin):
            return (self.OVERRIDEN_NAMES, self.NOT_OVERRIDEN_NAMES)

        def queryset(self, request, queryset):
            if self.value() in self.OVERRIDEN_NAMES:
                return queryset.filter(**filters.EventFilter.overriden())
            elif self.value() in self.NOT_OVERRIDEN_NAMES:
                return queryset.filter(**filters.EventFilter.not_overriden())
            
            return queryset

    
    list_display = ("subject_override", "date", "abstract_day", "time_slot_override")
    search_fields = ("participants_override__name", "subject_override__name", "places_override__building", "places_override__room", "kind_override__name", "date")
    list_filter = (EventOverridenFilter, "kind_override", "is_event_canceled")

    @admin.display(description=AbstractEvent._meta.get_field("abstract_day").verbose_name, 
                   ordering="name")
    def abstract_day(self, obj):
        return obj.abstract_event.abstract_day


@admin.register(AbstractEventChanges)
class AbstractEventChangesAdmin(BaseAdmin):
    list_display = ("datemodified", "__str__", "is_exported")
    list_filter = ("is_created", "is_deleted", "is_exported")

    actions = ["delete_exported", "export_selected", "export_not_exported"]

    @admin.action(description="Удалить экспортированные")
    def delete_exported(modeladmin, request, queryset):
        """Deletes already exported AbstractEventChanges
        """
        
        AbstractEventChanges.objects.filter(is_exported=True).delete()

        messages.success(request, "Успешно удалены")

    @admin.action(description="Экспортировать выбранное")
    def export_selected(modeladmin, request, queryset):
        """Export XLS form given AbstractEventChanges
        """
        
        response = WriteAPI.make_changes_file(queryset)

        messages.success(request, "Успешно экспортированы")

        return response

    @admin.action(description="Экспортировать не экспортированные")
    def export_not_exported(modeladmin, request, queryset):
        """Export XLS form all not exported AbstractEventChanges
        """

        changes = AbstractEventChanges.objects.filter(is_exported=False)

        if not changes.exists():
            messages.warning(request, "Нечего экспортировать: все изменения экспортированы")

            return

        response = WriteAPI.make_changes_file(changes)

        messages.success(request, "Успешно экспортированы")

        return response
        
    def changelist_view(self, request, extra_context = None):
        """Allows user to interact with specified actions without selecting models
        """
        
        if "action" in request.POST and request.POST["action"] in ["export_not_exported", "delete_exported"]:
            post = request.POST.copy()

            # makes request never empty
            post.update({ admin.helpers.ACTION_CHECKBOX_NAME : "0" })

            request._set_post(post)

        return super(AbstractEventChangesAdmin, self).changelist_view(request, extra_context)


@admin.register(AbstractEvent)
class AbstractEventAdmin(BaseAdmin):
    list_display = ("datemodified", "subject", "abstract_day", "time_slot")
    search_fields = ("participants__name", "subject__name", "places__building", "places__room", "kind__name")
    list_filter = ("kind__name",)

    actions = ["delete_events", "fill", "check_fields"]

    @admin.action(description="Удалить связанные события")
    def delete_events(modeladmin, request, queryset):
        """Deletes all Events related with given AbstractEvents
        """
        
        Event.objects.filter(abstract_event__in=queryset).delete()
        messages.success(request, "Связанные события успешно удалены")

    @admin.action(description="Заполнить семестр")
    def fill(modeladmin, request, queryset):
        """Fills semester with Events from given AbstractEvents
        """
        
        if WriteAPI.fill_event_table(queryset):
            messages.success(request, "Успешно заполнено")
        else:
            messages.error(request, "Произошла ошибка")

    @admin.action(description="Проверить на накладки в расписании")
    def check_fields(modeladmin, request, queryset):
        """Checks for double usage selected AbstractEvents field values
        """
        
        is_any_warning_shown = False

        for ae in queryset:
            is_double_usage_found, message = Utilities.check_abstract_event(ae)

            if is_double_usage_found:
                is_any_warning_shown = True

                messages.warning(request, message)

        if not is_any_warning_shown:
            messages.success(request, "В выбранных запланированных событиях накладки не найдены")


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
        """Applies selected DayDateOverrides
        """
        
        import api.utility_filters as filters

        for ddo in queryset:
            reader = ReadAPI(filters.DateFilter.from_singe_date(ddo.day_source))
            reader.add_filter(filters.EventFilter.by_department(ddo.department))
            
            reader.find_models(Event)
            
            for e in reader.get_found_models():
                WriteAPI.apply_date_override(ddo, e)

        messages.success(request, "Успешно перенесены")


@admin.register(EventCancel)
class EventCancelAdmin(BaseAdmin):
    list_display = ("date", "department")
    search_fields = ("date", "department")


TokenAdmin.raw_id_fields = ["user"]