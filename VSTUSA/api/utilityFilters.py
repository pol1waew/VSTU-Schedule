from django.db.models import F
from datetime import date, timedelta
from api.models import (
    Event,
)
import re


class UtilityFilterBase:
    """Base parent class for filters   

    Utility filters returns filter query: dict {field_name : parameter}
    """


class DateFilter(UtilityFilterBase):
    @staticmethod
    def from_singe_date(date_ : str|date):
        return {"date" : date_}

    @staticmethod
    def today():
        return DateFilter.from_singe_date(date.today())

    @staticmethod
    def tomorrow():
        return DateFilter.from_singe_date(date.today() + timedelta(days=1))

    @staticmethod
    def from_range(date_ : str|date, left_range : int, right_range : int):
        if isinstance(date_, str):
            date_ = date.fromisoformat(date_)
        
        left_interval_date = date_ - timedelta(days=left_range)
        right_interval_date = date_ + timedelta(days=right_range)

        return {"date__range" : [left_interval_date, right_interval_date]}
    
    @staticmethod
    def take_whole_week(date_):
        return DateFilter.from_range(date_, date_.weekday(), 6 - date_.weekday())

    @staticmethod
    def this_week():
        return DateFilter.take_whole_week(date.today())
    
    @staticmethod
    def next_week():
        return DateFilter.take_whole_week(date.today() + timedelta(weeks=1))
    

class ParticipantFilter(UtilityFilterBase):
    @staticmethod
    def by_name(name : str|list[str]):
        """
        Use list of participant names for OR behaviour
        """

        if type(name) is list:
            return {"participants_override__name__in" : name}
        
        return {"participants_override__name" : name}
        
    @staticmethod
    def by_role(role : str|list[str]):
        """
        Use list of participant roles for OR behaviour
        """
        
        if type(role) is list:
            return {"participants_override__role__in" : role}
        
        return {"participants_override__role" : role}
    

class PlaceFilter(UtilityFilterBase):
    @classmethod
    def by_repr(cls, repr : str|list[str]):
        """
        Use list of places repr for OR behaviour
        """

        building = []
        room = []

        for r in repr:
            splited = r.split(" ", 1)

            building.append(splited[0])
            room.append(splited[1])

        fitler_ = cls.by_building(building)
        fitler_.update(cls.by_room(room))

        return fitler_

    @staticmethod
    def by_building(building : str|list[str]):
        """
        Use list of place buildings for OR behaviour
        """

        if type(building) is list:
            return {"places_override__building__in" : building}

        return {"places_override__building" : building}

    @staticmethod
    def by_room(room : str|list[str]):
        """
        Use list of place rooms for OR behaviour
        """
        
        if type(room) is list:
            return {"places_override__room__in" : room}

        return {"places_override__room" : room}
    

class SubjectFilter(UtilityFilterBase):
    @staticmethod
    def by_name(name : str|list[str]):
        """
        Use list of subject names for OR behaviour
        """

        if type(name) is list:
            return {"subject_override__name__in" : name}

        return {"subject_override__name" : name}
    

class TimeSlotFilter(UtilityFilterBase):
    @staticmethod
    def by_repr(repr : str|list[str]):
        """
        Use list of time slots repr for OR behaviour
        """

        alt_name = []
        for r in repr:
            alt_name.append(re.search(r"\d{1,2}\D+\d{1,2}", r)[0])

        if type(repr) is list:
            return {"time_slot_override__alt_name__in" : alt_name}

        return {"time_slot_override__alt_name" : alt_name}
    

class KindFilter(UtilityFilterBase):
    @staticmethod
    def by_name(name : str|list[str]):
        """
        Use list of subject names for OR behaviour
        """

        if type(name) is list:
            return {"kind_override__name__in" : name}

        return {"kind_override__name" : name}


class EventFilter(UtilityFilterBase):
    @staticmethod
    def not_overriden():
        """
        Event overriden when at least one of fields (kind, subject, time slot, cancel)
        differ from AbstractEvent fields
        """
        
        return {
            "abstract_event__kind" : F("kind_override"),
            "abstract_event__subject" : F("subject_override"),
            "abstract_event__time_slot" : F("time_slot_override"),
            "is_event_canceled" : False
        }

    @staticmethod
    def by_schedule(schedule):
        return {"abstract_event__schedule" : schedule}

    @staticmethod
    def by_department(department):        
        return {"abstract_event__schedule__schedule_template__department" : department}
    

class AbstractEventFilter(UtilityFilterBase):
    @staticmethod
    def with_existing_events():
        return {"pk__in" : Event.objects.values_list("abstract_event__pk", flat=True).distinct()}
    