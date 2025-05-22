from django.db.models import QuerySet
from django.urls import reverse
from django.utils.html import format_html
from datetime import datetime, date, timedelta
import api.utility_filters as filters
from itertools import islice
import xlsxwriter
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
    MESSAGE_TEMPLATE = '<a href="{}">{}</a> / {}<br>'
    PARTICIPANTS_BASE_MESSAGE = "В сохранённом абс. событии ПРЕПОДАВАТЕЛИ одновременно участвуют в других абс. событиях:<br>"
    PARTICIPANT_MESSAGE_TEMPLATE = '<a href="{}">{}</a>, '
    PLACES_BASE_MESSAGE = "В сохранённом абс. событии АУДИТОРИИ одновременно задействованы в других абс. событиях:<br>"
    PLACE_MESSAGE_TEMPLATE = '<a href="{}">{}</a>, '


    @classmethod
    def check_abstract_event(cls, abstract_event : AbstractEvent):
        funcs = [Utilities.check_for_participants_duplicate, Utilities.check_for_places_duplicate]
        messages = []

        for f in funcs:
            state, message = f(abstract_event)
            
            if state:
                messages.append(message)

        return messages


    @classmethod
    def check_for_participants_duplicate(cls, abstract_event : AbstractEvent):
        other_aes = AbstractEvent.objects.filter(participants__in=abstract_event.participants.all(), 
                                                 abstract_day=abstract_event.abstract_day,
                                                 time_slot=abstract_event.time_slot).exclude(pk=abstract_event.pk).distinct()

        if not other_aes.exists():
            return False, None
        
        message = format_html(cls.PARTICIPANTS_BASE_MESSAGE)
        message_template = cls.MESSAGE_TEMPLATE
        participants_template = cls.PARTICIPANT_MESSAGE_TEMPLATE
        
        for ae in other_aes:
            p_urls = format_html("")
            
            for p in abstract_event.participants.filter(pk__in=ae.participants.values_list("pk", flat=True)):
                p_urls += format_html(participants_template, p.get_absolute_url(), str(p.name))
            p_urls = format_html(p_urls[:-2])
            
            message += format_html(message_template, ae.get_absolute_url(), str(ae), p_urls)

        return True, message
    
    @classmethod
    def check_for_places_duplicate(cls, abstract_event : AbstractEvent):
        other_aes = AbstractEvent.objects.filter(places__in=abstract_event.places.all(), 
                                                 abstract_day=abstract_event.abstract_day,
                                                 time_slot=abstract_event.time_slot).exclude(pk=abstract_event.pk).distinct()

        if not other_aes.exists():
            return False, None
        
        message = format_html(cls.PLACES_BASE_MESSAGE)
        message_template = cls.MESSAGE_TEMPLATE
        places_template = cls.PLACE_MESSAGE_TEMPLATE
        
        for ae in other_aes:
            p_urls = format_html("")
            
            for p in abstract_event.places.filter(pk__in=ae.places.values_list("pk", flat=True)):
                p_urls += format_html(places_template, p.get_absolute_url(), str(p))
            p_urls = format_html(p_urls[:-2])
            
            message += format_html(message_template, ae.get_absolute_url(), str(ae), p_urls)

        return True, message


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
        """Create new Event from abstract_event on specified date
        
        Needs to manualy aplly DayDateOverrides and EventCanceles after
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
    def get_semester_filling_parameters(abstract_event : AbstractEvent):
        """Intended for internal usage

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
    def fill_semester(cls, abstract_event : AbstractEvent):
        """Take abstract_event and fill semester
        """

        # creates single Event 
        # if abstract_event holds only on expected date
        if abstract_event.holds_on_date != None:
            cls.create_event(abstract_event.holds_on_date, abstract_event)
        else:
            semester_start_date, semester_end_date, date, repetition_period = cls.get_semester_filling_parameters(abstract_event)

            while date < semester_end_date:
                if date >= semester_start_date:
                    cls.create_event(date, abstract_event)
                
                    # creating Event for only first acceptable date
                    # if abstract_event is not repeatable
                    if not abstract_event.schedule.schedule_template.repeatable:
                        break
                
                date += timedelta(days=repetition_period)

        reader = ReadAPI({"department" : abstract_event.department})

        # getting all DayDateOverrides for abstract event
        reader.find_models(DayDateOverride)
        date_overrides = reader.get_found_models()

        reader.clear_filter_query()
        reader.add_filter({"abstract_event" : abstract_event})

        # applying date overrides to created events
        for ddo in date_overrides:
            reader.add_filter(filters.DateFilter.from_singe_date(ddo.day_source))
            
            reader.find_models(Event)
            
            if reader.get_found_models().exists():
                for e in reader.get_found_models():
                    cls.override_event_date(ddo, e)

            reader.remove_last_filter()

    @classmethod
    def fill_event_table(cls, abstract_events, full_clear = False):
        """Clear event table and fill it from abstract_events

        Use full_clear for clearing all event table
        instead events from abstract event
        """
        
        # deleting only not overriden events
        filter_query = filters.EventFilter.not_overriden()

        try:
            iterator = iter(abstract_events)
        except TypeError:
            # deleting Events only for specified AbstractEvents
            if not full_clear:
                filter_query.update({"abstract_event__pk" : abstract_events.pk})

            Event.objects.filter(**filter_query).delete()
            
            # filling semester by Events from abstract_event
            cls.fill_semester(abstract_events)
        else:
            # deleting Events only for specified AbstractEvents
            if not full_clear:
                filter_query.update({"abstract_event__in" : abstract_events})

            Event.objects.filter(**filter_query).delete()
            
            # filling semester by Events from abstract_event
            for ae in abstract_events:
                cls.fill_semester(ae)
                
        return True
    
    @classmethod
    def override_event_date(cls, override : DayDateOverride, event : Event):
        """Apply DayDateOverride to given events
        
        Use override=None to detach events from date override
        """

        if override:
            event.date = override.day_destination
            event.date_override = override      
        else:
            event.date = event.date_override.day_source
            event.date_override = None

        event.save()

    @staticmethod
    def update_event_canceling(event_cancel : EventCancel, event : Event, call_save_method : bool = True):
        """
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
    def export_changes_file(abs_event_changes):
        export_path = "change_files/"
        workbook = xlsxwriter.Workbook(f"{export_path}{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.xlsx")
        worksheet = workbook.add_worksheet()

        column_names = ["ГРУППА", "ДЕНЬ НЕДЕЛИ/УЧ. ЧАС", "ПРЕДМЕТ", "ИЗМЕНЕНО", "БЫЛО", "СТАЛО"]
        # дата создания change file поле - 1 колонка
        for i in range(len(column_names)):
            worksheet.write(0, i, column_names[i])

        row = 2
        for aec in abs_event_changes:
            data = aec.export()

            for changes in data:
                for i in range(len(changes)):
                    worksheet.write(row, i, changes[i])

                row += 1

            row += 1

        # удаление в отдельный action
        abs_event_changes.delete()
        
        worksheet.autofit()
        workbook.close()