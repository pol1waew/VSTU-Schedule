import django_filters

from api.models import Event, EventKind, EventParticipant, EventPlace, Schedule


class EventFilter(django_filters.FilterSet):
    schedule = django_filters.NumberFilter(field_name="schedule__id", label="ID расписания")

    date_from = django_filters.DateFilter(
        field_name="holdings__date",
        lookup_expr="gte",
        required=False,
        label="Поиск по дате проведения от",
    )
    date_to = django_filters.DateFilter(
        field_name="holdings__date",
        lookup_expr="lte",
        required=False,
        label="Поиск по дате проведения до",
    )
    time_from = django_filters.TimeFilter(
        field_name="holdings__time_slot__start_time",
        lookup_expr="gte",
        required=False,
        label="Время проведения от",
    )
    time_to = django_filters.TimeFilter(
        field_name="holdings__time_slot__end_time",
        lookup_expr="lte",
        required=False,
        label="Время проведения до",
    )
    participants = django_filters.ModelMultipleChoiceFilter(
        field_name="participants",
        queryset=EventParticipant.objects.all(),
        required=False,
        label="Участники",
    )
    can_have_kind = django_filters.ModelMultipleChoiceFilter(
        field_name="kind",
        queryset=EventKind.objects.all(),
        required=False,
        label="Фильтр видов занятий",
    )
    possible_rooms = django_filters.ModelMultipleChoiceFilter(
        field_name="holdings__place",
        queryset=EventPlace.objects.all(),
        required=False,
        label="Возможные места проведения",
    )

    class Meta:
        model = Event
        fields = [
            "schedule",
            "date_from",
            "date_to",
            "time_from",
            "time_to",
            "participants",
            "can_have_kind",
            "possible_rooms",
        ]


class ScheduleFilter(django_filters.FilterSet):
    faculty = django_filters.CharFilter(
        field_name="faculty", required=False, lookup_expr="icontains"
    )
    scope = django_filters.CharFilter(field_name="scope", required=False, lookup_expr="exact")
    course = django_filters.NumberFilter(required=False, field_name="course")
    semester = django_filters.NumberFilter(required=False, field_name="semester")
    has_events = django_filters.ModelMultipleChoiceFilter(
        field_name="events",
        queryset=Event.objects.all(),
        conjoined=True,
        method="filter_by_events",
        required=False,
        label="Имеют события",
    )

    class Meta:
        model = Schedule
        fields = [
            "schedule_template__metadata__faculty", 
            "schedule_template__metadata__scope", 
            "metadata__course", 
            "metadata__semester", 
            "metadata__years", 
            "has_events"
            ]

    def filter_by_events(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(events__in=value).distinct()
