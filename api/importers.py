import json
from api.utilities import Utilities
from rest_framework.exceptions import ValidationError
from api.models import (
    EventPlace,
    Department,
    Organization,
    EventParticipant,
    Subject,

    Event,
    EventKind,
    Schedule,
    TimeSlot,
)

# TODO: remove old logic
class JSONImporter:
    """
    Описание формата следует смотреть в классе ImportJSONAPIView в файле views.py
    """

    def __init__(self, json_data):
        self.json = json_data

    def _check_idnumber(self, item):
        if "idnumber" not in item:
            raise ValidationError(
                {
                    "idnumber": ["Требуется уникальный строковый идентификатор"],
                    "invalid_item": item,
                }
            )
        return True

    def import_data(self):
        try:
            self._import_data()
        except KeyError as e:
            raise ValidationError({str(e): ["Обязательное поле."]})

    def _import_data(self):
        data = self.json

        # Загрузка Subjects
        subjects = [
            Subject(idnumber=item["idnumber"], name=item["name"])
            for item in data.get("subjects", [])
            if self._check_idnumber(item)
        ]
        Subject.objects.bulk_create(
            subjects, update_conflicts=True, unique_fields=["idnumber"], update_fields=["name"]
        )

        # Загрузка EventKinds
        event_kinds = [
            EventKind(idnumber=item["idnumber"], name=item["name"])
            for item in data.get("event_kinds", [])
            if self._check_idnumber(item)
        ]
        EventKind.objects.bulk_create(
            event_kinds, update_conflicts=True, unique_fields=["idnumber"], update_fields=["name"]
        )

        # Загрузка TimeSlots
        time_slots = [
            TimeSlot(
                idnumber=item["idnumber"], start_time=item["start_time"], end_time=item["end_time"]
            )
            for item in data.get("time_slots", [])
            if self._check_idnumber(item)
        ]
        TimeSlot.objects.bulk_create(
            time_slots,
            update_conflicts=True,
            unique_fields=["idnumber"],
            update_fields=["start_time", "end_time"],
        )

        # Загрузка EventPlaces
        event_places = [
            EventPlace(idnumber=item["idnumber"], building=item["building"], room=item["room"])
            for item in data.get("event_places", [])
            if self._check_idnumber(item)
        ]
        EventPlace.objects.bulk_create(
            event_places,
            update_conflicts=True,
            unique_fields=["idnumber"],
            update_fields=["building", "room"],
        )

        # Загрузка EventParticipants
        event_participants = [
            EventParticipant(idnumber=item["idnumber"], name=item["name"], role=item["role"])
            for item in data.get("event_participants", [])
            if self._check_idnumber(item)
        ]
        EventParticipant.objects.bulk_create(
            event_participants,
            update_conflicts=True,
            unique_fields=["idnumber"],
            update_fields=["name", "role"],
        )

        # Загрузка Schedules
        schedules = [
            Schedule(
                idnumber=item["idnumber"],
                faculty=item["faculty"],
                scope=item["scope"],
                course=item["course"],
                semester=item["semester"],
                years=item["years"],
            )
            for item in data.get("schedules", [])
            if self._check_idnumber(item)
        ]
        Schedule.objects.bulk_create(
            schedules,
            update_conflicts=True,
            unique_fields=["idnumber"],
            update_fields=["faculty", "scope", "course", "semester", "years"],
        )

        # Загрузка Events
        events = []
        for item in data.get("events", []):
            self._check_idnumber(item)
            event = Event(
                idnumber=item["idnumber"],
                subject=Subject.objects.get(idnumber=item["subject_id"]),
                kind=EventKind.objects.get(idnumber=item["kind_id"]),
                schedule=Schedule.objects.get(idnumber=item["schedule_id"]),
            )
            events.append(event)

        Event.objects.bulk_create(
            events,
            update_conflicts=True,
            unique_fields=["idnumber"],
            update_fields=["subject", "kind", "schedule"],
        )


class EventImporter:
    pass


class ReferenceImporter:
    @staticmethod
    def import_place_reference(reference_data : str):
        json_data = json.loads(reference_data)

        all_normalized_places = []

        for place in json_data["places"]:
            normalized_place = Utilities.normalize_place_repr(place)

            if not normalized_place in all_normalized_places:
                all_normalized_places.append(normalized_place)

        places_to_create = []

        for place in all_normalized_places:
            places_to_create.append(
                EventPlace(
                    building=place[0],
                    room=place[1]
                )
            )

        if places_to_create:
            EventPlace.objects.bulk_create(places_to_create)

    @staticmethod
    def import_subject_reference(reference_data : str):
        json_data = json.loads(reference_data)

        subjects_to_create = []

        for entry in json_data:
            subjects_to_create.append(
                Subject(name=entry["discipline_name"])
            )
        
        if subjects_to_create:
            Subject.objects.bulk_create(subjects_to_create)

    @staticmethod
    def import_faculty_reference(reference_data : str):
        json_data = json.loads(reference_data)

        # TODO: looking baad
        organization = Organization.objects.get(name="ВолгГТУ")
        faculties_to_create = []

        for entry in json_data:
            faculties_to_create.append(
                Department(
                    name=entry["faculty_fullname"],
                    shortname=entry["faculty_shortname"],
                    code=entry["faculty_id"],
                    parent_department=None,
                    organization=organization
                )
            )
        
        if faculties_to_create:
            Department.objects.bulk_create(faculties_to_create)

    @staticmethod
    def import_department_reference(reference_data : str):
        json_data = json.loads(reference_data)

        # TODO: looking baad
        organization = Organization.objects.get(name="ВолгГТУ")
        departments_to_create = []

        for entry in json_data:
            try:
                parent_department = Department.objects.get(code=entry["faculty_id"])
            except Department.DoesNotExist:
                parent_department = None

            departments_to_create.append(
                Department(
                    name=entry["department_fullname"],
                    shortname=entry["department_shortname"],
                    code=entry["department_code"],
                    parent_department=parent_department,
                    organization=organization
                )
            )
        
        if departments_to_create:
            Department.objects.bulk_create(departments_to_create)

    @staticmethod
    def import_teacher_reference(reference_data : str):
        """

        Creates EventParticipant (teacher) even Department not found
        """

        json_data = json.loads(reference_data)

        teachers_to_create = []

        for entry in json_data:
            try:
                department = Department.objects.get(code=entry["staff_department_code"])
            except Department.DoesNotExist:
                department = None

            teachers_to_create.append(
                EventParticipant(
                    name="{surname} {name}{patronymic}".format(
                        surname=entry["staff_surname"],
                        name=f"{entry["staff_name"][0]}." if entry["staff_name"] else "",
                        patronymic=f"{entry["staff_patronymic"][0]}." if entry["staff_patronymic"] else ""
                    ),
                    role=EventParticipant.Role.TEACHER, ## TODO: assistant
                    is_group=False,
                    department=department
                )
            )
        
        if teachers_to_create:
            EventParticipant.objects.bulk_create(teachers_to_create)

    @staticmethod
    def import_student_reference(reference_data : str):
        """

        Creates EventParticipant (teacher) even Department not found
        """
        
        json_data = json.loads(reference_data)

        students_to_create = []

        for entry in json_data:
            try:
                department = Department.objects.get(code=entry["faculty_id"])
            except Department.DoesNotExist:
                department = None

            students_to_create.append(
                EventParticipant(
                    name=entry["group_name"],
                    role=EventParticipant.Role.STUDENT,
                    is_group=True,
                    department=department
                )
            )
        
        if students_to_create:
            EventParticipant.objects.bulk_create(students_to_create)
