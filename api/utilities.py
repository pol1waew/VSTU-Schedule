from django.db.models import QuerySet
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpResponse
from django.utils.safestring import SafeText
from datetime import datetime, date, timedelta
import api.utility_filters as filters
from itertools import islice
import xlsxwriter # TODO: replace with openpyxl
import io
import json
import re
from api.models import (
    CommonModel,
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


class Utilities:
    HEADER_MESSAGE_TEMPLATE = 'В запланированном событии <a href="{}">{}</a><br><br>'
    DUPLICATE_MESSAGE_TEMPLATE = '<a href="{}">{}</a> / {}<br>'
    PARTICIPANTS_BASE_MESSAGE = 'ПРЕПОДАВАТЕЛИ одновременно участвуют в других запланированных событиях:<br>'
    PARTICIPANT_MESSAGE_TEMPLATE = '<a href="{}">{}</a>, '
    PLACES_BASE_MESSAGE = 'АУДИТОРИИ одновременно задействованы в других запланированных событиях:<br>'
    PLACE_MESSAGE_TEMPLATE = '<a href="{}">{}</a>, '

    @classmethod
    def check_abstract_event(cls, abstract_event : AbstractEvent) -> tuple[bool, SafeText]:
        """Check given AbstractEvent for models double usage

        Returns:
            a tuple of state of double usage and message for user notification. 
            If no model duplicating found then message will be empty
        """
        
        funcs = [Utilities.check_for_participants_duplicate, Utilities.check_for_places_duplicate]
        message = format_html(cls.HEADER_MESSAGE_TEMPLATE, abstract_event.get_absolute_url(), str(abstract_event))
        is_anything_found = False

        for f in funcs:
            is_double_usage_found, m = f(abstract_event)
            
            if is_double_usage_found:
                is_anything_found = True

                message += m
                message += format_html("<br>")
        message = format_html(message[:-4])

        return is_anything_found, message

    @classmethod
    def check_for_participants_duplicate(cls, abstract_event : AbstractEvent) -> tuple[bool, SafeText|None]:
        """Checks for EventPartcipant double usage

        Returns:
            a tuple of state of double usage and message for user notification. 
            If EventParticipants not duplicating then message will be empty
        """

        other_aes = AbstractEvent.objects.filter(participants__in=abstract_event.participants.all(), 
                                                 abstract_day=abstract_event.abstract_day,
                                                 time_slot=abstract_event.time_slot).exclude(pk=abstract_event.pk).distinct()

        if not other_aes.exists():
            return False, None
        
        return_message = format_html(cls.PARTICIPANTS_BASE_MESSAGE)
        
        for ae in other_aes:
            p_urls = format_html("")
            
            for p in abstract_event.participants.filter(pk__in=ae.participants.values_list("pk", flat=True)):
                p_urls += format_html(cls.PARTICIPANT_MESSAGE_TEMPLATE, p.get_absolute_url(), str(p.name))
            p_urls = format_html(p_urls[:-2])
            
            return_message += format_html(cls.DUPLICATE_MESSAGE_TEMPLATE, ae.get_absolute_url(), str(ae), p_urls)

        return True, return_message
    
    @classmethod
    def check_for_places_duplicate(cls, abstract_event : AbstractEvent) -> tuple[bool, SafeText|None]:
        """Checks for EventPlace double usage

        Returns:
            a tuple of state of double usage and message for user notification. 
            If EventPlace not duplicating then message will be empty
        """
        
        other_aes = AbstractEvent.objects.filter(places__in=abstract_event.places.all(), 
                                                 abstract_day=abstract_event.abstract_day,
                                                 time_slot=abstract_event.time_slot).exclude(pk=abstract_event.pk).distinct()

        if not other_aes.exists():
            return False, None
        
        return_message = format_html(cls.PLACES_BASE_MESSAGE)
        
        for ae in other_aes:
            p_urls = format_html("")
            
            for p in abstract_event.places.filter(pk__in=ae.places.values_list("pk", flat=True)):
                p_urls += format_html(cls.PLACE_MESSAGE_TEMPLATE, p.get_absolute_url(), str(p))
            p_urls = format_html(p_urls[:-2])
            
            return_message += format_html(cls.DUPLICATE_MESSAGE_TEMPLATE, ae.get_absolute_url(), str(ae), p_urls)

        return True, return_message

    @staticmethod
    def normalize_place_repr(place_repr : str) -> tuple[str, str]|None:
        """Take place and convert it into acceptable format

        Place must be in format: {building}{room} separated by
        ' ' or ',' or '-'         
        
        Returns None if no room given

        If no building given, first string will be empty: ("", {room})
        """
        
        if place_repr is None:
            return None

        place = place_repr.strip()

        if not place:
            return None
        
        # SPACE should be always the last one
        for separator in [",", "-", " "]:
            if separator in place:
                building_part, room_part = place.split(separator, 1)
                building = building_part.strip()
                room = room_part.strip()

                if room:
                    return building, room
                
                return None

        return "", place

    @staticmethod
    def normalize_time_slot_repr(time_slot_repr : str) -> tuple[str, str, str]|None:
        """Take time slot and convert it into acceptable format

        Time slot must be present
            as alt name: \d-\d
            as start time: HH:MM or HH.MM
            as start and end times: START_TIME-END_TIME or START_TIME END_TIME

        Returns time slot structured as (ALT_NAME, START_TIME, END_TIME) 
        and formated as (\d-\d HH:MM HH:MM). Empty values equals ''
        """

        # 1-2
        # 3 -  4
        # exclude 8:30-10.00
        ALT_NAME_REG_EX = r"^\d{1,2}\s*\-+\s*\d{1,2}$"

        if time_slot_repr is None:
            return None
        
        time_slot = time_slot_repr.strip()

        if not time_slot:
            return None
        
        # check for alt_name format
        match_ = re.search(ALT_NAME_REG_EX, time_slot)

        if match_:
            return match_[0], "", ""
        
        time_slot = time_slot.replace(".", ":")

        for separator in ["-", " "]:
            if separator in time_slot:
                start_time, end_time = time_slot.split(separator, 1)

                return "", start_time.strip(), end_time.strip()
        
        return "", time_slot, ""

    @staticmethod
    def normalize_subject_name(name : str) -> str:
        return name.strip()

    @staticmethod
    def normalize_kind_name(kind : str) -> str:
        return kind.strip().capitalize()

    @staticmethod
    def normalize_scope(scope : str):
        return scope.strip().capitalize()

    @staticmethod
    def get_month_number(name : str):
        """Returns month number from month name
        """
        
        MONTHS = { 
            "январь" : 1, 
            "февраль" : 2, 
            "март" : 3, 
            "апрель" : 4, 
            "май" : 5, 
            "июнь" : 6, 
            "июль" : 7, 
            "август" : 8, 
            "сентябрь" : 9, 
            "октябрь" : 10, 
            "ноябрь": 11, 
            "декабрь" : 12
        }
        
        return MONTHS[name.lower()]
    
    @staticmethod
    def get_month_name(month_number : int|list[int]) -> str|None|list[str|None]:
        """Returns month name from month number

        Returns None for not-existing month number
        """
        
        MONTH_NAMES = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        
        if type(month_number) is list:
            names = []

            for i in month_number:
                names.append(
                    MONTH_NAMES[i - 1] 
                    if i >= 1 and i <= 12 
                    else None
                )

            return names

        return MONTH_NAMES[month_number - 1] if month_number >= 1 and month_number <= 12 else None

    @classmethod
    def get_scope_value(cls, scope_label : str) -> ScheduleTemplateMetadata.Scope:
        for scope in ScheduleTemplateMetadata.Scope:
            if scope.label == cls.normalize_scope(scope_label):
                return scope.value


class EventImportAPI:
    SUBJECT_NORMALIZATION_CAPITALIZE = False

    @staticmethod
    def _normalize_subject_name(name : str) -> str:
        return name.strip()

    @staticmethod
    def _normalize_kind_name(kind : str) -> str:
        return kind.strip().capitalize()

    @staticmethod
    def _normalize_participant_name(name : str) -> str:
        return name.strip()

    @classmethod
    def _collect_reference_data(cls, entries) -> dict:
        """Collects data from all entries in imported JSON
        """
        
        subjects : set[str] = set()
        kinds : set[str] = set()
        teacher_names : set[str] = set()
        group_names : set[str] = set()
        places : set[tuple[str, str]] = set()
        time_slots : set[str] = set()

        for entry in entries:
            subjects.add(cls._normalize_subject_name(entry["subject"]))
            kinds.add(cls._normalize_kind_name(entry["kind"]))

            for teacher_name in entry.get("participants", {}).get("teachers", []):
                normalized_teacher_name = cls._normalize_participant_name(teacher_name)

                if normalized_teacher_name:
                    teacher_names.add(normalized_teacher_name)

            for group_name in entry.get("participants", {}).get("student_groups", []):
                normalized_group_name = cls._normalize_participant_name(group_name)

                if normalized_group_name:
                    group_names.add(normalized_group_name)

            for place_repr in entry.get("places", []):
                normalized_place = Utilities.normalize_place_repr(place_repr)

                if normalized_place:
                    places.add(normalized_place)

            for time_slot_repr in entry.get("hours", []):
                normalized_time_slot = Utilities.normalize_time_slot_repr(time_slot_repr)

                if normalized_time_slot:
                    time_slots.add(normalized_time_slot)


        return {
            "subjects" : subjects,
            "kinds" : kinds,
            "teacher_names" : teacher_names,
            "group_names" : group_names,
            "places" : places,
            "time_slots" : time_slots
        }

    @classmethod
    def _ensure_reference_data(cls, reference_data : dict) -> None:
        """Creates models for non-existing inside database JSON data
        """
        
        if not reference_data:
            return

        subjects = reference_data.get("subjects", set())
        if subjects:
            existing_subjects = set(
                Subject.objects.filter(name__in=subjects).values_list("name", flat=True)
            )
            new_subjects = [
                Subject(name=name)
                for name in subjects
                if name not in existing_subjects
            ]
            if new_subjects:
                Subject.objects.bulk_create(new_subjects)

        kinds = reference_data.get("kinds", set())
        if kinds:
            existing_kinds = set(
                EventKind.objects.filter(name__in=kinds).values_list("name", flat=True)
            )
            new_kinds = [
                EventKind(name=name)
                for name in kinds
                if name not in existing_kinds
            ]
            if new_kinds:
                EventKind.objects.bulk_create(new_kinds)

        teacher_names = reference_data.get("teacher_names", set())
        group_names = reference_data.get("group_names", set())
        all_participant_names = teacher_names | group_names

        if all_participant_names:
            existing_participants = set(
                EventParticipant.objects.filter(name__in=all_participant_names).values_list("name", flat=True)
            )
            new_participants: list[EventParticipant] = []

            for name in teacher_names:
                if name in existing_participants:
                    continue
                new_participants.append(
                    EventParticipant(
                        name=name,
                        role=EventParticipant.Role.TEACHER,
                        is_group=False,
                        # TODO: add department
                    )
                )

            for name in group_names:
                if name in existing_participants:
                    continue
                new_participants.append(
                    EventParticipant(
                        name=name,
                        role=EventParticipant.Role.STUDENT,
                        is_group=True,
                        # TODO: add department
                    )
                )

            if new_participants:
                EventParticipant.objects.bulk_create(new_participants)

        places = reference_data.get("places", set())
        if places:
            rooms = {room for _, room in places}

            if rooms:
                existing_places = set(
                    EventPlace.objects.filter(room__in=rooms).values_list("building", "room")
                )
            else:
                existing_places = set()

            new_places = [
                EventPlace(building=building, room=room)
                for building, room in places
                if (building, room) not in existing_places
            ]

            if new_places:
                EventPlace.objects.bulk_create(new_places)

        #TODO: rewrite
        time_slots = reference_data.get("time_slots", set())
        if time_slots:
            filter_by_start_time, left_time_slots = filters.TimeSlotFilter.by_start_time([time_slot[1] for time_slot in time_slots])
            
            if filter_by_start_time:
                existing_time_slots = set(
                    TimeSlot.objects.filter(**filter_by_start_time).values_list("start_time", flat=True)
                )
            else:
                existing_time_slots = set()

            # At this moment, we not auto creating TimeSlots from alt_names
            """
            if left_time_slots:
                filter_by_alt_name, _ = filters.TimeSlotFilter.by_alt_name(left_time_slots)

                if filter_by_alt_name:
                    existing_time_slots.update(set(
                        TimeSlot.objects.filter(**filter_by_alt_name).values_list("alt_name", "start_time")
                    ))
            """
            
            new_time_slots = [
                TimeSlot(
                    alt_name=alt_name, 
                    start_time=datetime.strptime(start_time, "%H:%M"), 
                    end_time=datetime.strptime(end_time, "%H:%M") if end_time else None
                )
                for alt_name, start_time, end_time in time_slots
                if start_time and datetime.strptime(start_time, "%H:%M").time() not in existing_time_slots
            ]

            if new_time_slots:
                TimeSlot.objects.bulk_create(new_time_slots)

    @classmethod
    def import_event_data(cls, event_data : str):
        """Reads data from given file and fill database with new AbstractEvents and Events
        """
        
        json_data = json.loads(event_data)
        
        cls.make_event_import(
            json_data["title"],
            json_data["table"]["grid"],
            json_data["table"]["datetime"]["weeks"],
            json_data["table"]["datetime"]["week_days"],
            json_data["table"]["datetime"]["months"]
        )
    
    @classmethod
    def make_event_import(cls, title : str, entries, weeks, week_days : list[str], months : list[str]):
        """Applies data from loaded JSON on database
        """
        
        schedule = cls.find_schedule(title)
        reference_data = cls._collect_reference_data(entries)
        cls._ensure_reference_data(reference_data)
        reference_lookup = cls._build_reference_lookup(reference_data)
        global_calendar = cls.make_calendar(weeks, months, schedule)

        for entry in entries:
            cls.use_parsed_data(*cls.parse_data(entry, global_calendar, week_days, reference_lookup), schedule)
        
    @classmethod
    def make_calendar(cls, weeks, months : list[str], schedule : Schedule) -> dict:
        """
        
        parsed_weeks = { 
            week_id : { 
                week_day_index : [
                    dd.mm.YYYY,
                    dd.mm.YYYY...
                ]
            } 
        }

        Example:

        parsed_weeks = { 
            "first_week" : { 
                0 : [
                    1.02.2025,
                    15.02.2025
                ],
                1 : [
                    2.02.2025,
                    16.02.2025
                ]
            },
            "second_week" : { 
                0 : [
                    8.02.2025,
                    22.02.2025
                ],
                1 : [
                    9.02.2025,
                    23.02.2025
                ]
            } 
        }
        """

        normalized_weeks = {}
        if isinstance(weeks, dict):
            normalized_weeks = weeks
        elif isinstance(weeks, list):
            for week_entry in weeks:
                if isinstance(week_entry, dict):
                    for week_key, data in week_entry.items():
                        normalized_weeks[week_key] = data
        else:
            raise ValueError("Некорректный формат данных недель в JSON.")

        calendar = {}
        left_year, right_year = schedule.metadata.years.split("-", 1)

        for week_id in normalized_weeks.keys():
            calendar[week_id] = {}

            for week_day in normalized_weeks[week_id]:
                calendar[week_id][week_day["week_day_index"]] = []

                for month in week_day["calendar"]:
                    month_number = Utilities.get_month_number(months[month["month_index"]])

                    for month_day in month["month_days"]:
                        calendar[week_id][week_day["week_day_index"]].append(
                            datetime.strptime(
                                "{}.{}.{}".format(month_day, month_number, left_year if month_number > 6 else right_year), 
                                "%d.%m.%Y"
                            ).date()
                        )

        return calendar

    @classmethod
    def _build_reference_lookup(cls, ref_data: dict) -> dict:
        reference_lookup = {
            "subjects" : {},
            "kinds" : {},
            "participants" : {},
            "places" : {},
            "time_slots" : TimeSlot.objects.none()
        }

        subjects = ref_data.get("subjects", set())
        if subjects:
            subject_qs = Subject.objects.filter(name__in=list(subjects))
            reference_lookup["subjects"] = {}
            for subject in subject_qs:
                reference_lookup["subjects"].setdefault(subject.name, subject)

        kinds = ref_data.get("kinds", set())
        if kinds:
            kind_qs = EventKind.objects.filter(name__in=list(kinds))
            reference_lookup["kinds"] = {}
            for kind in kind_qs:
                reference_lookup["kinds"].setdefault(kind.name, kind)

        all_participants = ref_data.get("teacher_names", set()) | ref_data.get("group_names", set())
        if all_participants:
            participants_qs = EventParticipant.objects.filter(name__in=list(all_participants))
            reference_lookup["participants"] = {}
            for participant in participants_qs:
                reference_lookup["participants"].setdefault(participant.name, participant)

        places = ref_data.get("places", set())
        if places:
            rooms = {room for _, room in places}

            if rooms:
                place_queryset = EventPlace.objects.filter(room__in=rooms)

                reference_lookup["places"] = {
                    (place.building, place.room) : place for place in place_queryset
                }

        time_slots = ref_data.get("time_slots", set())
        if time_slots:
            start_times = {start_time for _, start_time, _ in time_slots if start_time}
            alt_names = {alt_name for alt_name, start_time, _ in time_slots if not start_time}
                        
            if start_times:
                reference_lookup["time_slots"] = TimeSlot.objects.filter(start_time__in=start_times)

            if alt_names:
                reference_lookup["time_slots"] |= TimeSlot.objects.filter(alt_name__in=alt_names)

            # reference_lookup["time_slots"].update({
            #     (
            #         time_slot.alt_name, 
            #         time_slot.start_time.strftime("%H:%M").removeprefix("0"), 
            #         time_slot.end_time.strftime("%H:%M").removeprefix("0") if time_slot.end_time else ""
            #     ) : time_slot for time_slot in time_slot_queryset_from_start_times | time_slot_queryset_from_alt_names
            # })

        return reference_lookup

    @classmethod
    def parse_data(cls, entry, global_calendar, week_days : list[str], reference_lookup : dict):
        """Finds existing models for JSON data

        Method uses pre-prepared reference data
        """

        week_id = entry["week"]
        week_day_index = entry["week_day_index"]

        kind_name = cls._normalize_kind_name(entry["kind"])
        kind = reference_lookup["kinds"].get(kind_name)
        if kind is None:
            raise EventKind.DoesNotExist(f"Тип события '{kind_name}' не найден после подготовки справочников.")

        subject_name = cls._normalize_subject_name(entry["subject"])
        subject = reference_lookup["subjects"].get(subject_name)
        if subject is None:
            raise Subject.DoesNotExist(f"Предмет '{subject_name}' не найден после подготовки справочников.")

        participants = []
        missing_participants = []

        for teacher_name in entry.get("participants", {}).get("teachers", []):
            normalized = cls._normalize_participant_name(teacher_name)
            participant = reference_lookup["participants"].get(normalized)
            if participant:
                participants.append(participant)
            else:
                missing_participants.append(normalized)

        for group_name in entry.get("participants", {}).get("student_groups", []):
            normalized = cls._normalize_participant_name(group_name)
            participant = reference_lookup["participants"].get(normalized)
            if participant:
                participants.append(participant)
            else:
                missing_participants.append(normalized)

        if missing_participants:
            raise EventParticipant.DoesNotExist(
                f"Не удалось найти участников: {', '.join(missing_participants)}"
            )

        places = []
        missing_places = []
        for place_repr in entry.get("places", []):
            normalized_place = Utilities.normalize_place_repr(place_repr)

            if not normalized_place:
                continue

            place = reference_lookup["places"].get(normalized_place)
            if place:
                places.append(place)
            else:
                missing_places.append(place_repr)

        if missing_places:
            raise EventPlace.DoesNotExist(
                f"Не удалось найти аудитории: {', '.join(missing_places)}"
            )

        abstract_day = AbstractDay.objects.get(
            name__startswith=1 if week_id == "first_week" else 2,
            name__endswith=week_days[week_day_index].capitalize()
        )

        time_slots = []
        missing_time_slots = []
        for time_slot_repr in entry.get('hours', []):
            normalized_time_slot = Utilities.normalize_time_slot_repr(time_slot_repr)

            if not normalized_time_slot:
                continue
            
            ## TODO: select timeslot with alt_name > without altname
            time_slot = reference_lookup["time_slots"].filter(
                **filters.TimeSlotFilter.by_repr(normalized_time_slot[1] if normalized_time_slot[1] else normalized_time_slot[0])
            ).first()

            if time_slot:
                time_slots.append(time_slot)
            else:
                missing_time_slots.append(time_slot_repr)

        if missing_time_slots:
            raise TimeSlot.DoesNotExist(
                f"Не найден учебный час для значений: {', '.join(missing_time_slots)}"
            )
        
        holds_on_date_values = entry.get("holds_on_date") or []
        if holds_on_date_values:
            holds_on_dates = []

            for date_ in holds_on_date_values:
                holds_on_dates.append(datetime.strptime(date_, "%d.%m.%Y").date())
        else:
            holds_on_dates = [ None ]

        calendar = global_calendar[week_id][week_day_index]

        return kind, subject, participants, places, abstract_day, time_slots, holds_on_dates, calendar
  
    @staticmethod
    def use_parsed_data(kind : EventKind, 
                        subject : Subject,
                        participants : list[EventParticipant],
                        places : list[EventPlace],
                        abstract_day : AbstractDay,
                        time_slots : list[TimeSlot],
                        holds_on_dates : list[date]|list[None],
                        calendar : dict,
                        schedule : Schedule):
        """Creates AbstractEvents and Events for given TimeSlots and dates (if needed)
        """

        for date_ in holds_on_dates:
            for time_slot in time_slots:
                created_abstract_event = WriteAPI.create_abstract_event(
                    kind,
                    subject,
                    participants,
                    places,
                    abstract_day,
                    time_slot,
                    date_,
                    schedule
                )

                WriteAPI.fill_semester_by_dates(created_abstract_event, calendar)
        
    ## TODO: write tests
    @staticmethod
    def find_schedule(title : str) -> Schedule:
        """Parse timetable title and find Schedule based on this title

        Schedule must already exist. 
        Title must contain course, faculty, semester and years information

        Returns found Schedule

        Returns:
            schedule
        """
        
        # 4 курса
        # 4 курс
        # 4курса
        # 4   курса
        COURSE_REG_EX = r"(\d)\s*курса?"
        # ФЭВТ
        # ТК
        # курсФЭВТна
        FACULTY_REG_EX = r"[А-ЯЁ]{2,}"
        # 2 семестр
        # 2семестр
        # 2   семестр
        SEMESTER_REG_EX = r"(\d)\s*семестр"
        # 2024-2025
        FULL_YEARS_REG_EX = r"(\d{4}-\d{4})"
        # Бакалавры
        # бакалавриат
        # магистратура
        # Аспирантура
        # консульт.
        SCOPE_REG_EX = r"(([бБ]акалавр|[мМ]агистр|[аА]спирант|[кК]онсульт)[а-яА-ЯёЁ]*)"

        filter_query = {}

        course_match = re.search(COURSE_REG_EX, title, flags=re.IGNORECASE)
        if course_match:
            filter_query["metadata__course"] = int(course_match.group(1))

        faculty_tokens = re.findall(FACULTY_REG_EX, title)
        if faculty_tokens:
            filter_query["schedule_template__metadata__faculty__iexact"] = faculty_tokens[-1]

        semester_match = re.search(SEMESTER_REG_EX, title, flags=re.IGNORECASE)
        if semester_match:
            filter_query["metadata__semester"] = int(semester_match.group(1))

        years_match = re.search(FULL_YEARS_REG_EX, title)
        if years_match:
            filter_query["metadata__years"] = years_match.group(1)

        scope_match = re.search(SCOPE_REG_EX, title)
        if scope_match:
            filter_query["schedule_template__metadata__scope"] = Utilities.get_scope_value(
                Utilities.normalize_scope(scope_match.group(1))
            )

        if not filter_query:
            raise ValueError(
                f"Не удалось извлечь параметры расписания из заголовка '{title}'. "
                "Убедитесь, что он содержит хотя бы номер курса и сокращение факультета."
            )
        
        filter_query["status"] = Schedule.Status.ACTIVE

        schedules = Schedule.objects.filter(**filter_query)

        if not schedules.exists():
            raise Schedule.DoesNotExist(
                f"Расписание с параметрами {filter_query} не найдено. "
                f"Заголовок: '{title}'."
            )

        if schedules.count() > 1:
            raise Schedule.MultipleObjectsReturned(
                f"Найдено несколько расписаний, удовлетворяющих параметрам {filter_query}. "
                "Уточните заголовок или дополните его семестром и учебным годом."
            )

        return schedules.first()


class ReadAPI:
    filter_query : dict
    found_models : QuerySet

    def __init__(self, filter_query : dict = None):
        self.filter_query = filter_query or {}

    def add_filter(self, filter : filters.UtilityFilterBase):
        """Updates filter query by adding new filter

        Allows user manualy append filters in format {'field_name' : value}
        """
        
        self.filter_query.update(filter)

    def remove_filter(self, index : int):
        if index < len(self.filter_query):
            del self.filter_query[next(islice(self.filter_query, index, None))]

    def remove_first_filter(self):
        self.remove_filter(0)

    def remove_last_filter(self):
        self.remove_filter(len(self.filter_query) - 1)

    def clear_filter_query(self):
        self.filter_query = {}

    def find_models(self, model : CommonModel):
        """Finds filtered models
        """
        
        self.found_models = model.objects.filter(**self.filter_query)

    def get_found_models(self):
        """Returns found models

        Can be empty if nothing found
        """
        
        return self.found_models
    
    @staticmethod
    def get_all_teachers():
        return EventParticipant.objects.filter(role__in=[EventParticipant.Role.TEACHER, EventParticipant.Role.ASSISTANT])
    
    @staticmethod
    def get_all_groups():
        return EventParticipant.objects.filter(is_group=True)
    
    @staticmethod
    def get_all_places():
        return EventPlace.objects.all()
    
    @staticmethod
    def get_all_subjects():
        return Subject.objects.all()
    
    @staticmethod
    def get_all_kinds():
        return EventKind.objects.all()
    
    @staticmethod
    def get_all_time_slots():
        return TimeSlot.objects.all()


class WriteAPI:
    @staticmethod
    def create_event(date_ : str|date, abstract_event : AbstractEvent):
        """Creates new Event from abstract_event on specified date
        """

        if isinstance(date_, str):
            date_ = date.fromisoformat(date_)

        event = Event()
        
        event.date = date_
        event.kind_override = abstract_event.kind
        event.subject_override = abstract_event.subject
        event.time_slot_override = abstract_event.time_slot
        event.abstract_event = abstract_event
        event.is_event_canceled = False
        
        event.save()

        event.participants_override.add(*abstract_event.participants.all())
        event.places_override.add(*abstract_event.places.all())

    @staticmethod
    def create_abstract_event(kind : EventKind, 
                              subject : Subject,
                              participants : list[EventParticipant],
                              places : list[EventPlace],
                              abstract_day : AbstractDay,
                              time_slot : TimeSlot,
                              holds_on_date : date|None,
                              schedule : Schedule) -> AbstractEvent:
        """Creates new Abstract Event

        Returns created Abstract Event

        Returns:
            abstract_event
        """

        abstract_event = AbstractEvent()

        abstract_event.kind = kind
        abstract_event.subject = subject
        abstract_event.abstract_day = abstract_day
        abstract_event.time_slot = time_slot
        if holds_on_date:
            abstract_event.holds_on_date = holds_on_date
        abstract_event.schedule = schedule

        abstract_event.save()

        abstract_event.participants.add(*participants)
        abstract_event.places.add(*places)

        return abstract_event
        
    @staticmethod
    def get_semester_filling_parameters(abstract_event : AbstractEvent):
        """Intended for internal usage
        
        Returns semester filling parameters for given AbstarctEvent

        Returns:
            semester_start_date, 
            semester_end_date,
            fill_from_date,
            repetition_period
        """
        
        semester_start_date = abstract_event.schedule.start_date

        fill_from_date = semester_start_date

        # finding first week monday date

        # if start date in first week
        # finding previous first week monday date
        if abstract_event.schedule.starting_day_number.day_number < 7:
            fill_from_date -= timedelta(abstract_event.schedule.starting_day_number.day_number)
        # otherwise
        # finding next first week monday date
        else:
            fill_from_date += timedelta(14 - abstract_event.schedule.starting_day_number.day_number)

        # adding abstract_event delta from first week monday
        fill_from_date += timedelta(abstract_event.abstract_day.day_number)

        return semester_start_date, \
                abstract_event.schedule.end_date, \
                fill_from_date, \
                abstract_event.schedule.schedule_template.repetition_period

    @classmethod
    def fill_semester_by_repeating(cls, abstract_event : AbstractEvent):
        """Creates Events from given AbstractEvent for every semester working day
        using Schedule parameters
        """

        # creates single Event 
        # if abstract_event holds only on expected date
        if abstract_event.holds_on_date != None:
            cls.create_event(abstract_event.holds_on_date, abstract_event)
        else:
            semester_start_date, semester_end_date, date_, repetition_period = cls.get_semester_filling_parameters(abstract_event)

            while date_ < semester_end_date:
                if date_ >= semester_start_date:
                    cls.create_event(date_, abstract_event)
                
                    # creating Event for only first acceptable date
                    # if abstract_event is not repeatable
                    if not abstract_event.schedule.schedule_template.repeatable:
                        break
                
                date_ += timedelta(days=repetition_period)
        
        cls.check_for_day_date_override(abstract_event)

    @classmethod
    def fill_semester_by_dates(cls, abstract_event : AbstractEvent, dates : list[date]):
        """Creates Events from given AbstractEvent for every given date

        Always creates Events even if it goes out of bounds the semester
        """

        # creates single Event 
        # if abstract_event holds only on expected date
        if abstract_event.holds_on_date != None:
            cls.create_event(abstract_event.holds_on_date, abstract_event)
        else:
            for date_ in dates:
                cls.create_event(date_, abstract_event)
        
        cls.check_for_day_date_override(abstract_event)

    @classmethod
    def check_for_day_date_override(cls, abstract_event : AbstractEvent):
        reader = ReadAPI({"department" : abstract_event.department})

        # getting all DayDateOverrides for AbstractEvent
        reader.find_models(DayDateOverride)
        date_overrides = reader.get_found_models()

        reader.clear_filter_query()
        reader.add_filter({"abstract_event" : abstract_event})

        # applying date overrides to Events
        for ddo in date_overrides:
            reader.add_filter(filters.DateFilter.from_singe_date(ddo.day_source))
            
            reader.find_models(Event)
            
            if reader.get_found_models().exists():
                for e in reader.get_found_models():
                    cls.apply_date_override(ddo, e)

            reader.remove_last_filter()

    @staticmethod
    def apply_date_override(date_override : DayDateOverride, event : Event, call_save_method : bool = True):
        """Apply DayDateOverride to given Event
        
        Use date_override=None to detach Event from date override
        """

        if date_override:
            event.date = date_override.day_destination
            event.date_override = date_override      
        else:
            event.date = event.date_override.day_source

        if call_save_method:
            event.save()

    @classmethod
    def fill_event_table(cls, abstract_event):
        """Clear Event table and fill it from given AbstractEvent
        """
        
        # deleting only not overriden events
        filter_query = filters.EventFilter.not_overriden()

        try:
            iterator = iter(abstract_event)
        # working with single AbstractEvent
        except TypeError:
            # deleting Events only for specified AbstractEvent
            filter_query.update({"abstract_event__pk" : abstract_event.pk})

            Event.objects.filter(**filter_query).delete()
            
            # filling semester by Events from abstract_event
            cls.fill_semester_by_repeating(abstract_event)
        # working with lsit of AbstractEvents
        else:
            # deleting Events only for specified AbstractEvents
            filter_query.update({"abstract_event__in" : abstract_event})

            Event.objects.filter(**filter_query).delete()
            
            # filling semester by Events from every AbstractEvent
            for ae in abstract_event:
                cls.fill_semester_by_repeating(ae)
                
        return True
    
    @staticmethod
    def update_events(abstract_event : AbstractEvent, update_non_m2m : bool = True, update_m2m : bool = True):
        """Refresh fields of Events with given AbstractEvent
        """
        
        if not update_non_m2m and not update_m2m:
            return
        
        filter_query = {"abstract_event" : abstract_event}
        filter_query.update(filters.EventFilter.not_overriden())

        for e in Event.objects.filter(**filter_query):
            if update_non_m2m:
                e.kind_override = abstract_event.kind
                e.subject_override = abstract_event.subject
                e.time_slot_override = abstract_event.time_slot

            if update_m2m:
                e.participants_override.clear()
                e.participants_override.add(*abstract_event.participants.all())
                e.places_override.clear()
                e.places_override.add(*abstract_event.places.all())

            e.save()
    
    @staticmethod
    def apply_event_canceling(event_cancel : EventCancel, event : Event, call_save_method : bool = True):
        """Apply EventCancel to given Event

        Use event_cancel=None to undo event cancel
        """

        if event_cancel:
            event.is_event_canceled = True
            event.event_cancel = event_cancel
        else:
            event.is_event_canceled = False
            event.event_cancel = None
            
        if call_save_method:
            event.save()

    @staticmethod
    def make_changes_file(abs_event_changes) -> HttpResponse|None:
        """Makes XLS file for given AbstractEventChanges
        """
        
        if not abs_event_changes.exists():
            return None
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        column_names = ["ДАТА СОЗДАНИЯ", "ГРУППА", "ДЕНЬ НЕДЕЛИ/УЧ. ЧАС", "ПРЕДМЕТ", "ИЗМЕНЕНО", "БЫЛО", "СТАЛО"]
        for i in range(len(column_names)):
            worksheet.write(0, i, column_names[i])

        row = 2
        for aec in abs_event_changes:
            for changes in aec.export():
                for i in range(len(changes)):
                    worksheet.write(row, i, changes[i])

                row += 1

            row += 1
        
        worksheet.autofit()
        workbook.close()

        output.seek(0)

        response = HttpResponse(output, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f"attachment; filename={datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.xlsx"

        return response
    
    # TODO: tests
    @staticmethod
    def create_common_abstract_days() -> bool:
        ABSTRACT_DAYS_DATA = [
            (0, "1 неделя, Понедельник"),
            (1, "1 неделя, Вторник"),
            (2, "1 неделя, Среда"),
            (3, "1 неделя, Четверг"),
            (4, "1 неделя, Пятница"),
            (5, "1 неделя, Суббота"),
            (6, "1 неделя, Воскресенье"),
            (7, "2 неделя, Понедельник"),
            (8, "2 неделя, Вторник"),
            (9, "2 неделя, Среда"),
            (10, "2 неделя, Четверг"),
            (11, "2 неделя, Пятница"),
            (12, "2 неделя, Суббота"),
            (13, "2 неделя, Воскресенье")
        ]
        abstract_days_to_create = []

        for data in ABSTRACT_DAYS_DATA:
            try:
                AbstractDay.objects.get(day_number=data[0], name=data[1])
            except AbstractDay.DoesNotExist:
                abstract_days_to_create.append(
                    AbstractDay(day_number=data[0], name=data[1])
                )
        
        if abstract_days_to_create:
            AbstractDay.objects.bulk_create(abstract_days_to_create)

            return True
        
        return False

    @staticmethod
    def create_common_time_slots() -> bool:
        TIME_SLOTS_DATA = [
            ("1-2", "08:30", "10:00"),
            ("3-4", "10:10", "11:40"),
            ("5-6", "11:50", "13:20"),
            ("7-8", "13:40", "15:10"),
            ("9-10", "15:20", "16:50"),
            ("11-12", "17:00", "18:30"),
        ]
        time_slots_to_create = []

        for data in TIME_SLOTS_DATA:
            try:
                TimeSlot.objects.get(
                    alt_name=data[0],
                    start_time=data[1],
                    end_time=data[2]
                )
            except TimeSlot.DoesNotExist:
                time_slots_to_create.append(
                    TimeSlot(
                        alt_name=data[0],
                        start_time=data[1],
                        end_time=data[2]
                    )
                )
        
        if time_slots_to_create:
            TimeSlot.objects.bulk_create(time_slots_to_create)

            return True
        
        return False
