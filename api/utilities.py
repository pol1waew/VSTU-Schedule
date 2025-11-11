from django.db.models import QuerySet
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpResponse
from django.utils.safestring import SafeText
from datetime import datetime, date, timedelta
import api.utility_filters as filters
from itertools import islice
import xlsxwriter
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


class ImportAPI:
    @classmethod
    def import_data(cls, data_file_path : str) -> int:
        """Reads data from given file and fill database with new Events
        """
        
        try:
            with open(data_file_path, mode="r", encoding="utf8") as data_file:
                data = json.load(data_file)
            
        except FileNotFoundError or FileExistsError:
            return 1
        
        cls.make_import(
            data["title"],
            data["table"]["grid"],
            data["table"]["datetime"]["weeks"],
            data["table"]["datetime"]["week_days"],
            data["table"]["datetime"]["months"]
        )

        return 0
    
    @classmethod
    def make_import(cls, title : str, entries, weeks, week_days : list[str], months : list[str]):
        """Applies data from loaded JSON on database
        """
        
        schedule = cls.get_schedule(title)
        global_calendar = cls.make_calendar(weeks, months, schedule)

        for entry in entries:
            cls.use_parsed_data(*cls.parse_data(entry, global_calendar, week_days), schedule)
        
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

        calendar = {}
        left_year, right_year = schedule.metadata.years.split("-", 1)

        for week_id in weeks.keys():
            calendar[week_id] = {}

            for week_day in weeks[week_id]:
                calendar[week_id][week_day["week_day_index"]] = []

                for month in week_day["calendar"]:
                    month_number = cls.get_month_number(months[month["month_index"]])

                    for month_day in month["month_days"]:
                        calendar[week_id][week_day["week_day_index"]].append(
                            datetime.strptime(
                                "{}.{}.{}".format(month_day, month_number, left_year if month_number > 6 else right_year), 
                                "%d.%m.%Y"
                            ).date()
                        )

        return calendar
    
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

    @classmethod
    def parse_data(cls, entry, global_calendar, week_days : list[str]):
        """Finds existing models for JSON data

        Method does not create new models except AbstractEvent and its Events!

        All data found in JSON, such as EventKind, Subject or EventParticipants, 
        must already exists in database as models
        """

        event_participant_names = entry["participants"]["teachers"] + entry["participants"]["student_groups"]

        week_id = entry["week"]
        week_day_index = entry["week_day_index"]

        kind = EventKind.objects.get(name=entry["kind"].capitalize())
        subject = Subject.objects.get(name=entry["subject"])
        participants = EventParticipant.objects.filter(name__in=event_participant_names).all()
        places = EventPlace.objects.filter(**filters.PlaceFilter.by_repr(entry["places"])).all()
        abstract_day = AbstractDay.objects.get(
            name__startswith=1 if week_id == "first_week" else 2,
            name__endswith=week_days[week_day_index].capitalize()
        )
        time_slots = TimeSlot.objects.filter(**filters.TimeSlotFilter.by_repr(entry["hours"]))
        if entry["holds_on_date"]:
            holds_on_dates = []

            for date_ in entry["holds_on_date"]:
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
        

    @staticmethod
    def get_schedule(title : str) -> Schedule:
        """Parse timetable title and find Schedule based on this title

        Schedule must already exist. 
        Title must contain course, faculty, semester and years information

        Returns found Schedule

        Returns:
            schedule
        """
        
        COURSE_REG_EX = r"(\d) курса"
        FACULTY_REG_EX = r"курса ([А-Я]+)"
        SEMESTER_REG_EX = r"(\d) семестр"
        FULL_YEARS_REG_EX = r"(\d{4}-\d{4}) учебного"

        course = re.search(COURSE_REG_EX, title).group(1)
        faculty = re.search(FACULTY_REG_EX, title).group(1)
        semester = re.search(SEMESTER_REG_EX, title).group(1)
        years = re.search(FULL_YEARS_REG_EX, title).group(1)

        return Schedule.objects.get(**filters.ScheduleFilter.by_base_parameters(
            course,
            faculty,
            semester,
            years
        ))


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