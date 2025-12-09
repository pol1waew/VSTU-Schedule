import json
import re
from datetime import datetime, date, timedelta
from api.utilities import Utilities, ReadAPI, WriteAPI
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
    AbstractEvent,
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
        
        schedule = cls.find_schedule(Utilities.replace_all_roman_with_arabic_numerals(title))
        reference_lookup : dict = {}

        for entry in entries:
            cls.correct_event_data(schedule, entry)

            reference_data = cls.collect_reference_data(entry)
            cls.ensure_reference_data(reference_data)
            reference_lookup.update(cls.build_reference_lookup(reference_data)) ## TODO: test

            calendar = cls.make_calendar(weeks, months, schedule)

            cls.create_events(
                schedule,
                *cls.parse_data(entry, calendar, week_days, reference_lookup)
            )

    @classmethod
    def correct_event_data(cls, schedule : Schedule, event_data) -> None:
        """Corrects inaccuracies and defects in given event_data

        "places": [
          "Б--514"
        ]
        """

        corrected_holds_on_date = cls.correct_holds_on_date_data(schedule, event_data["holds_on_date"])

        if corrected_holds_on_date:
            event_data["holds_on_date"] = corrected_holds_on_date

    @staticmethod
    def correct_holds_on_date_data(schedule : Schedule, holds_on_date : list[str]) -> list[str]|None:
        """Replaces ".." and ";" in holds_on_date with correct dates

        Returns corrected sorted list holds_on_date of unique dates
        
        Returns None when nothing changed
        """

        # 03.09.2024
        COMMON_DATE_REG_EX = r"\d{1,2}.\d{1,2}.\d{4}"

        # 03.09..01.10
        DOUBLE_RANGE_DATE_REG_EX = r"(\d{1,2}.\d{1,2})..(\d{1,2}.\d{1,2})"

        # с 03.09
        # с03.09
        # с   03.09
        SINGLE_RANGE_DATE_REG_EX = r"с\s*(\d{1,2}.\d{1,2})"

        # 03.09
        #   03.09
        DAY_MONTH_DATE_REG_EX = r"(\d{1,2}.\d{1,2})"

        LEFT_YEAR, RIGHT_YEAR = schedule.metadata.years.split("-", 1)
        is_something_corrected = False
        corrected_holds_on_date : set[str] = set()

        for date_ in holds_on_date:
            if re.search(COMMON_DATE_REG_EX, date_):
                corrected_holds_on_date.add(date_)

                continue

            if ";" in date_:
                for splited_date in date_.split(";"):
                    day, month = splited_date.strip().split(".", 1)

                    corrected_holds_on_date.add("{}.{}.{}".format(day, month, LEFT_YEAR if int(month) > 6 else RIGHT_YEAR))

                is_something_corrected = True    

                continue

            match = re.search(DOUBLE_RANGE_DATE_REG_EX, date_)

            if match:
                from_day, from_month = match.group(1).split(".", 1)
                to_day, to_month = match.group(2).split(".", 1)

                from_date = datetime.strptime(
                    "{}.{}.{}".format(from_day, from_month, LEFT_YEAR if int(from_month) > 6 else RIGHT_YEAR), 
                    "%d.%m.%Y"
                ).date()
                to_date = datetime.strptime(
                    "{}.{}.{}".format(to_day, to_month, LEFT_YEAR if int(from_month) > 6 else RIGHT_YEAR), 
                    "%d.%m.%Y"
                ).date()

                while from_date <= to_date:
                    corrected_holds_on_date.add(datetime.strftime(from_date, "%d.%m.%Y"))

                    from_date += timedelta(days=schedule.schedule_template.repetition_period)

                is_something_corrected = True

                continue

            match = re.search(SINGLE_RANGE_DATE_REG_EX, date_)

            if match:
                from_day, from_month = match.group(1).split(".", 1)

                from_date = datetime.strptime(
                    "{}.{}.{}".format(from_day, from_month, LEFT_YEAR if int(from_month) > 6 else RIGHT_YEAR), 
                    "%d.%m.%Y"
                ).date()

                while from_date <= schedule.end_date:
                    corrected_holds_on_date.add(datetime.strftime(from_date, "%d.%m.%Y"))

                    from_date += timedelta(days=schedule.schedule_template.repetition_period)

                is_something_corrected = True

                continue

            match = re.search(DAY_MONTH_DATE_REG_EX, date_)

            if match:
                day, month = match.group(1).strip().split(".", 1)

                corrected_holds_on_date.add("{}.{}.{}".format(day, month, LEFT_YEAR if int(month) > 6 else RIGHT_YEAR))

                is_something_corrected = True    

                continue

            raise ValueError(f"Неправильный формат даты '{date_}' в holds_on_date '{holds_on_date}'.")

        return list(sorted(corrected_holds_on_date)) if is_something_corrected else None

    @staticmethod
    def collect_reference_data(event_data) -> dict:
        subjects : set[str] = set()
        kinds : set[str] = set()
        teachers : set[str] = set()
        groups : set[str] = set()
        places : set[tuple[str, str]] = set()
        time_slots : set[str] = set()

        subjects.add(Utilities.normalize_subject_name[event_data["subject"]])

        kinds.add(Utilities.normalize_kind_name[event_data["kind"]])

        for teacher in event_data.get("participants", {}).get("teachers", []):
            normalizaed_teacher = Utilities.normalize_participant_name(teacher)

            if normalizaed_teacher:
                teachers.add(normalizaed_teacher)
                
        for group in event_data.get("participants", {}).get("groups", []):
            normalizaed_group = Utilities.normalize_participant_name(group)

            if normalizaed_group:
                groups.add(normalizaed_group)

        for place in event_data.get("places", []):
            normalizaed_place = Utilities.normalize_place_repr(place)

            if normalizaed_place:
                places.add(normalizaed_place)

        for time_slot in event_data.get("hours", []):
            normalizaed_time_slot = Utilities.normalize_time_slot_repr(time_slot)

            if normalizaed_time_slot:
                time_slots.add(normalizaed_time_slot)

        return {
            "subjects" : subjects,
            "kinds" : kinds,
            "teachers" : teachers,
            "groups" : groups,
            "places" : places,
            "time_slots" : time_slots
        }

    @staticmethod
    def ensure_reference_data(reference_data : dict) -> None:
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

        Title must contain course, faculty, scope, semester and years information
        """
        
        # 4 курса
        # 4 курс
        # 4курса
        # 4   курса
        # 1ый курс
        # 5-ого курса
        # 3-го курса
        COURSE_REG_EX = r"(\d)(\-?[а-яА-ЯёЁ]*)?\s*курса?"

        # ФЭВТ
        # ТК
        # курсФЭВТна
        # TODO: ФАСТиВ
        FACULTY_REG_EX = r"[А-ЯЁ]{2,}"

        # Бакалавры
        # бакалавриат
        # магистров
        # Аспирантура
        # консульт.
        SCOPE_REG_EX = r"(([бБ]акалавр|[мМ]агистр|[аА]спирант|[кК]онсульт)[а-яА-ЯёЁ]*)"

        # 2 семестр
        # 2семестр
        # 2   семестр
        # 2-ой семестр
        # 2-й семестр
        # 1ый семестр
        ARABIC_NUMERALS_SEMESTER_REG_EX = r"(\d)(\-?[а-яА-ЯёЁ]*)?\s*семестра?"
        
        # 2024-2025
        # 2024 -  2025
        FULL_YEARS_REG_EX = r"(\d{4}\s*-\s*\d{4})"
        
        reader = ReadAPI()

        course_match = re.search(COURSE_REG_EX, title, flags=re.IGNORECASE)
        if course_match:
            reader.add_filter({"metadata__course" : int(course_match.group(1))})

        faculty_matches = re.findall(FACULTY_REG_EX, title)
        if not faculty_matches:
            raise ValueError(f"Не удалось извлечь подразделение или факультет из заголовка '{title}'.")

        is_faculty_found = False
        
        for match in faculty_matches:
            try:
                Department.objects.get(shortname=match)
            except Department.DoesNotExist:
                continue
            
            # take first existing faculty from title
            reader.add_filter({"schedule_template__metadata__faculty__iexact" : match})

            is_faculty_found = True

            break

        if not is_faculty_found:
            raise ValueError(f"Не удалось найти подходящее подразделение или факультет для заголовка '{title}'.")

        scope_match = re.search(SCOPE_REG_EX, title)
        if scope_match:
            reader.add_filter({"schedule_template__metadata__scope" : Utilities.get_scope_value(
                Utilities.normalize_scope(scope_match.group(1))
            )})

        semester_match = re.search(ARABIC_NUMERALS_SEMESTER_REG_EX, title, flags=re.IGNORECASE)
        if semester_match:
            reader.add_filter({"metadata__semester" : int(semester_match.group(1))})

        full_years_match = re.search(FULL_YEARS_REG_EX, title)
        if full_years_match:
            reader.add_filter({"metadata__years" : full_years_match.group(1).replace(" ", "")})

        if not reader.has_any_filter_added():
            raise ValueError(f"Не удалось извлечь параметры расписания из заголовка '{title}'.")
        
        reader.add_filter({"status" : Schedule.Status.ACTIVE})
        reader.find_models(Schedule)

        if not reader.is_any_model_found():
            raise Schedule.DoesNotExist(
                f"Расписание с параметрами {reader.get_filter_query()} не найдено."
                f"Заголовок: '{title}'."
            )
        
        if not reader.is_single_model_found():
            raise Schedule.MultipleObjectsReturned(
                f"Найдено несколько расписаний, удовлетворяющих параметрам {reader.get_filter_query()}."
                "Уточните заголовок."
            )
        
        return reader.get_found_models().first()

    @staticmethod
    def make_calendar(weeks, months : list[str], schedule : Schedule) -> dict:
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

        normalized_weeks = {}

        if not len(weeks):
            raise ValueError("Отсутствуют данные недель в импортируемом файле.")

        if isinstance(weeks, dict):
            normalized_weeks = weeks
        elif isinstance(weeks, list):
            for week in weeks:
                if isinstance(week, dict):
                    for key, data in week.items():
                        normalized_weeks[key] = data
                else:
                    raise ValueError("Некорректный формат данных недель в импортируемом файле.")
        else:
            raise ValueError("Некорректный формат данных недель в импортируемом файле.")

        calendar = {}

        LEFT_YEAR, RIGHT_YEAR = schedule.metadata.years.split("-", 1)

        for key in normalized_weeks.keys():
            calendar[key] = {}

            for week_day in normalized_weeks[key]:
                calendar[key][week_day["week_day_index"]] = []

                for month in week_day["calendar"]:
                    month_number = Utilities.get_month_number(months[month["month_index"]])

                    for month_day in month["month_days"]:
                        calendar[key][week_day["week_day_index"]].append(
                            datetime.strptime(
                                "{}.{}.{}".format(month_day, month_number, LEFT_YEAR if month_number > 6 else RIGHT_YEAR), 
                                "%d.%m.%Y"
                            ).date()
                        )

        return calendar

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
                      calendar : list[date]) -> None:
        """Creates AbstractEvents and Events for given TimeSlots and dates

        Not create duplicates
        """

        for date_ in holds_on_dates:
            for time_slot in time_slots:
                if ReadAPI.is_abstract_event_already_exists(
                    kind, subject, participants, places, abstract_day, time_slot, date_, schedule
                ):
                    continue
                
                created_abstract_event = WriteAPI.create_abstract_event(
                    kind, subject, participants, places, abstract_day, time_slot, date_, schedule
                )

                WriteAPI.fill_semester_by_dates(created_abstract_event, calendar)


class ReferenceImporter:
    @staticmethod
    def import_place_reference(reference_data : str):
        """

        Not create duplicates
        """

        json_data = json.loads(reference_data)

        places_to_create = []
        already_read_places = []

        for place in json_data["places"]:
            normalized_place = Utilities.normalize_place_repr(place)

            if normalized_place in already_read_places or ReadAPI.is_place_already_exists(*normalized_place):
                continue

            places_to_create.append(
                EventPlace(
                    building=normalized_place[0],
                    room=normalized_place[1]
                )
            )
            
            already_read_places.append(normalized_place)

        if places_to_create:
            EventPlace.objects.bulk_create(places_to_create)

    @staticmethod
    def import_subject_reference(reference_data : str):
        """

        Not create duplicates
        """

        json_data = json.loads(reference_data)

        subjects_to_create = []
        already_read_subjects = []

        for entry in json_data:
            subject = entry["discipline_name"]
            
            if subject in already_read_subjects or ReadAPI.is_subject_already_exists(subject):
                continue

            subjects_to_create.append(
                Subject(name=subject)
            )
            
            already_read_subjects.append(subject)
        
        if subjects_to_create:
            Subject.objects.bulk_create(subjects_to_create)

    @staticmethod
    def import_faculty_reference(reference_data : str):
        """

        Not create duplicates
        """

        json_data = json.loads(reference_data)

        # TODO: looking baad
        organization = Organization.objects.get(name="ВолгГТУ")
        faculties_to_create = []
        already_read_faculties = []

        for entry in json_data:
            department_name = entry["faculty_fullname"]
            department_shortname = entry["faculty_shortname"]
            department_code = entry["faculty_id"]

            if (department_name, department_shortname, department_code) in already_read_faculties \
                or ReadAPI.is_department_already_exists(department_name, department_shortname, department_code):
                continue

            faculties_to_create.append(
                Department(
                    name=department_name,
                    shortname=department_shortname,
                    code=department_code,
                    parent_department=None,
                    organization=organization
                )
            )

            already_read_faculties.append((department_name, department_shortname, department_code))
        
        if faculties_to_create:
            Department.objects.bulk_create(faculties_to_create)

    @staticmethod
    def import_department_reference(reference_data : str):
        """

        Creates Department even parent_department not found

        Not create duplicates
        """

        json_data = json.loads(reference_data)

        # TODO: looking baad
        organization = Organization.objects.get(name="ВолгГТУ")
        departments_to_create = []
        already_read_departments = []

        for entry in json_data:
            department_name = entry["department_fullname"]
            department_shortname = entry["department_shortname"]
            department_code = entry["department_code"]

            if (department_name, department_shortname, department_code) in already_read_departments \
                or ReadAPI.is_department_already_exists(department_name, department_shortname, department_code):
                continue

            try:
                parent_department = Department.objects.get(code=entry["faculty_id"])
            except Department.DoesNotExist:
                parent_department = None

            departments_to_create.append(
                Department(
                    name=department_name,
                    shortname=department_shortname,
                    code=department_code,
                    parent_department=parent_department,
                    organization=organization
                )
            )

            already_read_departments.append((department_name, department_shortname, department_code))
        
        if departments_to_create:
            Department.objects.bulk_create(departments_to_create)

    @staticmethod
    def import_teacher_reference(reference_data : str):
        """

        Creates EventParticipant (teacher) even Department not found

        Can create duplicates when teachers have same names (surname and name, patronymic abbreviations)
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
                    name=Utilities.format_participant_name(
                        entry["staff_surname"], 
                        entry["staff_name"], 
                        entry["staff_patronymic"]
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

        Creates EventParticipant (student) even Department not found

        Not create duplicates
        """
        
        json_data = json.loads(reference_data)

        students_to_create = []
        already_read_students = []

        for entry in json_data:
            try:
                department = Department.objects.get(code=entry["faculty_id"])
            except Department.DoesNotExist:
                department = None

            student_name = entry["group_name"]

            if student_name in already_read_students or ReadAPI.is_participant_already_exists(student_name, department):
                continue

            students_to_create.append(
                EventParticipant(
                    name=student_name,
                    role=EventParticipant.Role.STUDENT,
                    is_group=True,
                    department=department
                )
            )
            already_read_students.append(student_name)
        
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
