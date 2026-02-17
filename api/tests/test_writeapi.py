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

"""py manage.py test api.tests.test_writeapi
"""

class TestWriteAPI(TestCase):
    def setUp(self):
        FACULTY_REFERENCE_DATA = """
        [
            {
                "faculty_id" : "111",
                "faculty_fullname" : "ФАКУЛЬТЕТ",
                "faculty_code" : "000000111",
                "faculty_shortname" : "ФАКУЛЬТ"
            }
        ]
        """
        DEPARTMENT_REFERENCE_DATA = """
            [
                {
                    "department_id" : "0",
                    "department_code" : "000000000",
                    "department_fullname" : "ПОДРАЗДЕЛЕНИЕ",
                    "department_shortname" : "ПОДРАЗД",
                    "faculty_id" : "111",
                    "faculty_shortname" : "ФАКУЛЬТ"
                }
            ]
        """
        SCHEDULE_REFERENCE_DATA = """
            [
                {
                    "course": "1",
                    "schedule_template_metadata_faculty_shortname": "ФАКУЛЬТ",
                    "semester": "2",
                    "years": "2025-2026",
                    "start_date": "09.02.2026",
                    "end_date": "07.06.2026",
                    "scope": "Магистратура",
                    "department_shortname": "ФАКУЛЬТ"
                }
            ]
        """

        WriteAPI.create_common_abstract_days()
        WriteAPI.create_common_time_slots()
        Organization.objects.create(name="ВолгГТУ")
        ReferenceImporter.import_faculty_reference(FACULTY_REFERENCE_DATA)
        ReferenceImporter.import_department_reference(DEPARTMENT_REFERENCE_DATA)
        ReferenceImporter.import_schedule(SCHEDULE_REFERENCE_DATA, True)

    def test_get_semester_filling_parameters(self):
        SCHEDULE = Schedule.objects.get(
            schedule_template__metadata__faculty="ФАКУЛЬТ", 
            schedule_template__metadata__scope=ScheduleTemplateMetadata.Scope.MASTER,
            metadata__course=1,
            metadata__semester=2
        )
        KIND = EventKind.objects.create(name="Лекция")
        SUBJECT = Subject.objects.create(name="ПРЕДМЕТ")
        DEPARTMENT = Department.objects.get(shortname="ФАКУЛЬТ")
        PARTICIPANTS = [
            EventParticipant.objects.create(
                name="Преподаватель И.О.",
                role=EventParticipant.Role.TEACHER,
                is_group=False,
                department=DEPARTMENT
            ),
            EventParticipant.objects.create(
                name="Группа-123",
                role=EventParticipant.Role.STUDENT,
                is_group=True,
                department=DEPARTMENT
            )
        ]
        PLACES = [EventPlace.objects.create(building="КОРПУС", room="123")]
        ABS_EVENT = AbstractEvent.objects.create(
            kind=KIND,
            subject=SUBJECT,
            abstract_day=AbstractDay.objects.get(day_number=9),
            time_slot=TimeSlot.objects.get(
                alt_name="1-2", 
                start_time="08:30", 
                end_time="10:00"
            ),
            schedule=SCHEDULE
        )
        ABS_EVENT.participants.set(PARTICIPANTS)
        ABS_EVENT.places.set(PLACES)

        #TODO
        print(WriteAPI.get_semester_filling_parameters(ABS_EVENT))
