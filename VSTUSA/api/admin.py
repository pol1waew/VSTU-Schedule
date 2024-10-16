from django.contrib import admin
from django.forms import BaseInlineFormSet
from django.utils import timezone

from api.models import (
    Event,
    EventHolding,
    EventKind,
    EventParticipant,
    EventPlace,
    Schedule,
    Subject,
)

from rest_framework.authtoken.admin import TokenAdmin


class EventHoldingInlineFormSet(BaseInlineFormSet):
    pass


class EventHoldingInline(admin.TabularInline):
    model = EventHolding
    formset = EventHoldingInlineFormSet
    extra = 1
    can_delete = True
    fields = ("date", "place", "time_slot")
    readonly_fields = ()


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


@admin.register(Schedule)
class ScheduleAdmin(BaseAdmin):
    list_display = ("faculty", "course", "semester", "years")
    search_fields = ("faculty", "scope")
    list_filter = ("faculty", "course", "semester", "years")


@admin.register(Event)
class EventAdmin(BaseAdmin):
    list_display = ("subject", "kind")
    search_fields = ("subject__name", "kind__name")
    list_filter = ("kind",)
    inlines = [EventHoldingInline]


TokenAdmin.raw_id_fields = ["user"]