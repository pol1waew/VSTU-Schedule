from datetime import datetime
from django.test import TestCase
from api.importers import ReferenceImporter
from api.utilities import WriteAPI, ReadAPI
from api.models import (
    Schedule,
    ScheduleTemplate,
    ScheduleMetadata,
    ScheduleTemplateMetadata,
    EventParticipant,
    Department,
    Organization,
    AbstractDay,
    TimeSlot,
    AbstractEvent,
    Event,
    EventPlace,
    Subject,
    EventKind
)

"""py manage.py test api.tests.test_readapi
"""

class TestReadAPI(TestCase):
    def setUp(self):
        FACULTY_REFERENCE_DATA = """
        [
            {
                "faculty_id" : "111",
                "faculty_fullname" : "Факультет электроники и вычислительной техники",
                "faculty_code" : "000000111",
                "faculty_shortname" : "ФЭВТ"
            }
        ]
        """
        SCHEDULE_REFERENCE_DATA = """
            [
                {
                    "course": "4",
                    "schedule_template_metadata_faculty_shortname": "ФЭВТ",
                    "semester": "2",
                    "years": "2024-2025",
                    "start_date": "01.09.2024",
                    "end_date": "01.02.2025",
                    "scope": "Бакалавриат",
                    "department_shortname": "ФЭВТ"
                }
            ]
        """

        WriteAPI.create_common_abstract_days()
        WriteAPI.create_common_time_slots()
        Organization.objects.create(name="ВолгГТУ")
        ReferenceImporter.import_faculty_reference(FACULTY_REFERENCE_DATA)
        ReferenceImporter.import_schedule(SCHEDULE_REFERENCE_DATA, True)

    def test_is_abstract_event_already_exists(self):
        DEPARTMENT = Department.objects.get(shortname="ФЭВТ")
        KIND = EventKind.objects.create(name="Лекция")
        SUBJECT = Subject.objects.create(name="ВКР")
        PARTICIPANTS = [
            EventParticipant.objects.create(
                name="Гилка В.В.",
                role=EventParticipant.Role.TEACHER,
                is_group=False,
                department=DEPARTMENT
            ),
            EventParticipant.objects.create(
                name="Кузнецова А.С.",
                role=EventParticipant.Role.TEACHER,
                is_group=False,
                department=DEPARTMENT
            ),
            EventParticipant.objects.create(
                name="ПрИн-466",
                role=EventParticipant.Role.STUDENT,
                is_group=True,
                department=DEPARTMENT
            ),
            EventParticipant.objects.create(
                name="ПрИн-467",
                role=EventParticipant.Role.STUDENT,
                is_group=True,
                department=DEPARTMENT
            )
        ]
        PLACES = [
            EventPlace.objects.create(building="В", room="902"),
            EventPlace.objects.create(building="В", room="903")
        ]
        ABSTRACT_DAY = AbstractDay.objects.get(day_number=0)
        TIME_SLOT = TimeSlot.objects.get(alt_name="1-2")
        DATE_ = datetime.strptime("1.02.2025", "%d.%m.%Y").date()
        SCHEDULE = Schedule.objects.get(
            schedule_template__metadata__faculty="ФЭВТ", 
            schedule_template__metadata__scope=ScheduleTemplateMetadata.Scope.BACHELOR,
            metadata__course=4,
            metadata__semester=2
        )

        WriteAPI.create_abstract_event(
            KIND, SUBJECT, PARTICIPANTS, PLACES, ABSTRACT_DAY, TIME_SLOT, None, SCHEDULE
        )
        WriteAPI.create_abstract_event(
            KIND, SUBJECT, PARTICIPANTS, PLACES, ABSTRACT_DAY, TIME_SLOT, DATE_, SCHEDULE
        )

        self.assertEqual(
            ReadAPI.is_abstract_event_already_exists(
                KIND, SUBJECT, PARTICIPANTS, PLACES, ABSTRACT_DAY, TIME_SLOT, DATE_, SCHEDULE
            ),
            True
        )
        self.assertEqual(
            ReadAPI.is_abstract_event_already_exists(
                KIND, SUBJECT, PARTICIPANTS, PLACES, ABSTRACT_DAY, TIME_SLOT, None, SCHEDULE
            ),
            True
        )

        OTHER_PARTICIPANT = EventParticipant.objects.create(
            name="ПрИн-467",
            role=EventParticipant.Role.STUDENT,
            is_group=True,
            department=DEPARTMENT
        )

        self.assertEqual(
            ReadAPI.is_abstract_event_already_exists(
                KIND, SUBJECT, [OTHER_PARTICIPANT], PLACES, ABSTRACT_DAY, TIME_SLOT, None, SCHEDULE
            ),
            False
        )
