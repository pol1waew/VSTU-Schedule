import json
from datetime import datetime, date
from api.utilities import Utilities
from rest_framework.exceptions import ValidationError
from api.models import (
    EventPlace,
    Department,
    Organization,
    EventParticipant,
    Subject,
    AbstractDay,
    ScheduleTemplateMetadata,
    ScheduleTemplate,
    ScheduleMetadata,
    Schedule,

    Event,
    EventKind,
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
    @classmethod
    def import_events(cls, event_data : str):
        """Import AbstractEvents and Events from given data
        """

        json_data = json.loads(event_data)
        
        cls.make_import(
            json_data["title"],
            json_data["table"]["grid"],
            json_data["table"]["datetime"]["weeks"],
            json_data["table"]["datetime"]["week_days"],
            json_data["table"]["datetime"]["months"]
        )

    @classmethod
    def make_import(cls, 
                    title : str, 
                    entries, 
                    weeks, 
                    week_days : list[str], 
                    months : list[str]):
        """Applies data on database
        """
        
        schedule = cls.find_schedule(title)
        reference_lookup : dict = {}

        """
        for entry in entries:
        
            reference_data = cls.collect_reference_data(entry)
            ensure_reference_data(reference_data)
            reference_lookup += cls.build_reference_lookup(reference_data)

            cls.create_events(
                schedule,
                *cls.parse_data(entry)
            )

        """        

        pass

    @staticmethod
    def collect_reference_data(event_data):
        """Collects data from Event data
        """

        pass

    @staticmethod
    def ensure_reference_data(event_data) -> None:
        """Creates models for Event data that not exist in database
        """

        pass

    @staticmethod
    def build_reference_lookup(reference_data : dict) -> dict:
        """Finds models for reference_data
        """
        
        pass

    @staticmethod
    def find_schedule(title : str) -> Schedule:
        """Finds Schedule from given title. If Schedule not exists then creates it

        Title must contain course, faculty, semester and years information
        """
        
        pass

    @staticmethod
    def make_calendar(weeks,
                      months : list[str],
                      years : str) -> dict:
        """Makes calendar of dates for Event creating in format:

        parsed_weeks = { 
            week_id : { 
                week_day_index : [
                    dd.mm.YYYY,
                    dd.mm.YYYY...
                ]
            } 
        }
        """

        pass

    @staticmethod
    def parse_data(event_data, 
                   calendar, 
                   week_days : list[str], 
                   reference_lookup : dict) -> tuple[
                       EventKind, 
                       Subject, 
                       list[EventParticipant], 
                       list[EventPlace],
                       list[AbstractDay],
                       list[TimeSlot],
                       list[date],
                       list[date]
                    ]:
        """Finds existing models for Event data

        Raise DoesNotExist if model not found
        """
        
        pass

    @staticmethod
    def create_events(schedule : Schedule,
                      kind : EventKind, 
                      subject : Subject,
                      participants : list[EventParticipant],
                      places : list[EventPlace],
                      abstract_day : AbstractDay,
                      time_slots : list[TimeSlot],
                      holds_on_dates : list[date]|list[None],
                      calendar : dict):
        """Creates AbstractEvents and Events for given TimeSlots and dates
        """

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

    @staticmethod
    def import_schedule(reference_data : str, save_archive_schedules : bool):
        json_data = json.loads(reference_data)

        for entry in json_data:
            scope_value = Utilities.get_scope_value(entry["scope"])

            if not scope_value:
                raise ValueError(f"Степень обучения '{entry["scope"]}' не найдена.")
            
            try:
                schedule_template_metadata = ScheduleTemplateMetadata.objects.get(
                    faculty=entry["schedule_template_metadata_faculty_shortname"],
                    scope=scope_value
                )
            except ScheduleTemplateMetadata.DoesNotExist:
                schedule_template_metadata = ScheduleTemplateMetadata.objects.create(
                    faculty=entry["schedule_template_metadata_faculty_shortname"],
                    scope=scope_value
                )

            try:
                department_ = Department.objects.get(shortname=entry["department_shortname"])
            except Department.DoesNotExist:
                raise Department.DoesNotExist(f"Подразделение '{entry["department_shortname"]}' не найдено.")
            
            try:
                schedule_template = ScheduleTemplate.objects.get(
                    metadata=schedule_template_metadata,
                    department=department_
                )
            except ScheduleTemplate.DoesNotExist:
                schedule_template = ScheduleTemplate.objects.create(
                    metadata=schedule_template_metadata,
                    repetition_period=14,
                    repeatable=True,
                    aligned_by_week_day=1,
                    department=department_
                )            

            try:
                schedule_metadata = ScheduleMetadata.objects.get(
                    years=entry["years"],
                    course=entry["course"],
                    semester=entry["semester"]
                )
            except ScheduleMetadata.DoesNotExist:
                schedule_metadata = ScheduleMetadata.objects.create(
                    years=entry["years"],
                    course=entry["course"],
                    semester=entry["semester"]
                )

            try:
                if not save_archive_schedules:
                    Schedule.objects.filter(
                        metadata=schedule_metadata,
                        schedule_template=schedule_template,
                        status=Schedule.Status.ARCHIVE
                    ).delete()
            except Schedule.DoesNotExist:
                pass

            try:
                existing_schedule = Schedule.objects.get(
                    metadata=schedule_metadata,
                    schedule_template=schedule_template,
                    status=Schedule.Status.ACTIVE
                )

                existing_schedule.status = Schedule.Status.ARCHIVE
                existing_schedule.save()
            except Schedule.DoesNotExist:
                pass

            Schedule.objects.create(
                metadata=schedule_metadata,
                status=Schedule.Status.ACTIVE,
                start_date=datetime.strptime(entry["start_date"], "%d.%m.%Y"),
                end_date=datetime.strptime(entry["end_date"], "%d.%m.%Y"),
                starting_day_number=AbstractDay.objects.get(day_number=0),
                schedule_template=schedule_template
            )
