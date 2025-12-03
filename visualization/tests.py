from django.test import TestCase
from api.models import (
    Event,
    EventParticipant,
    EventPlace,
    Subject,
    EventKind,
    TimeSlot,
    AbstractEvent,
    Schedule,
    ScheduleMetadata,
    ScheduleTemplate,
    ScheduleTemplateMetadata,
    Department,
    Organization,
    AbstractDay,
)
from visualization.logic import is_same_entries, get_row_spans


class MergeLogicTests(TestCase):
    """
    Минимальные тесты:
    - одинаковые события в одном и том же слоте сливаются,
    - события в разных слотах не сливаются,
    - тройные дубликаты дают rowSpan [3, 0, 0].
    """

    def setUp(self):
        org = Organization.objects.create(name="Орг")
        dept = Department.objects.create(name="Кафедра", shortname="Каф", code="K", organization=org)
        tmpl_meta = ScheduleTemplateMetadata.objects.create(
            faculty="ФЭВТ", scope=ScheduleTemplateMetadata.Scope.BACHELOR
        )
        sched_meta = ScheduleMetadata.objects.create(years="2024-2025", course=1, semester=1)
        day0 = AbstractDay.objects.create(day_number=0, name="1 неделя, Понедельник")
        tmpl = ScheduleTemplate.objects.create(
            metadata=tmpl_meta,
            repetition_period=7,
            repeatable=True,
            aligned_by_week_day=1,
            department=dept,
        )
        schedule = Schedule.objects.create(
            metadata=sched_meta,
            status=Schedule.Status.ACTIVE,
            start_date="2024-09-01",
            end_date="2025-01-31",
            starting_day_number=day0,
            schedule_template=tmpl,
        )

        self.subject = Subject.objects.create(name="СИСТЕМНАЯ ИНЖЕНЕРИЯ")
        self.kind = EventKind.objects.create(name="Лабораторная работа")
        self.teacher = EventParticipant.objects.create(
            name="Тест Преподаватель", role=EventParticipant.Role.TEACHER, is_group=False, department=dept
        )
        self.group = EventParticipant.objects.create(
            name="САПР-1.1", role=EventParticipant.Role.STUDENT, is_group=True, department=dept
        )
        self.place = EventPlace.objects.create(building="В", room="208")

        self.ts_1520 = TimeSlot.objects.create(alt_name="9-10", start_time="15:20", end_time="16:50")
        self.ts_1700 = TimeSlot.objects.create(alt_name="11-12", start_time="17:00", end_time="18:30")

        ae = AbstractEvent.objects.create(
            kind=self.kind,
            subject=self.subject,
            abstract_day=day0,
            time_slot=self.ts_1520,
            schedule=schedule,
        )
        ae.participants.add(self.teacher, self.group)
        ae.places.add(self.place)

        self.event1 = Event.objects.create(
            date="2024-12-08",
            kind_override=self.kind,
            subject_override=self.subject,
            time_slot_override=self.ts_1520,
            abstract_event=ae,
        )
        self.event1.participants_override.add(self.teacher, self.group)
        self.event1.places_override.add(self.place)

        self.event2 = Event.objects.create(
            date="2024-12-08",
            kind_override=self.kind,
            subject_override=self.subject,
            time_slot_override=self.ts_1520,
            abstract_event=ae,
        )
        self.event2.participants_override.add(self.teacher, self.group)
        self.event2.places_override.add(self.place)

        self.event3 = Event.objects.create(
            date="2024-12-08",
            kind_override=self.kind,
            subject_override=self.subject,
            time_slot_override=self.ts_1700,
            abstract_event=ae,
        )
        self.event3.participants_override.add(self.teacher, self.group)
        self.event3.places_override.add(self.place)

    def test_same_time_events_are_merged(self):
        self.assertTrue(is_same_entries(self.event1, self.event2))

    def test_different_time_events_not_merged(self):
        self.assertFalse(is_same_entries(self.event1, self.event3))

    def test_row_spans_for_triple_duplicates(self):
        row_spans = get_row_spans([[self.event1, self.event1, self.event1]])
        self.assertEqual(row_spans, [[3, 0, 0]])
