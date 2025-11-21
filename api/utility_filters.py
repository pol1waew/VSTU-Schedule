from datetime import date, timedelta
import re
from api.models import (Event,)


class UtilityFilterBase:
    """Base parent class for filters   

    Utility filters returns filter query in format: dict {field_name : parameter}
    """


class DateFilter(UtilityFilterBase):
    """Only for work with Event model fields
    """

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
    def from_date(from_date : str|date, to_date : str|date):
        if isinstance(from_date, str):
            from_date = date.fromisoformat(from_date)
        
        if isinstance(to_date, str):
            to_date = date.fromisoformat(to_date)
        
        return {"date__range" : [from_date, to_date]}
    
    @staticmethod
    def around_date(date_ : str|date, left_range : int, right_range : int):
        if isinstance(date_, str):
            date_ = date.fromisoformat(date_)
        
        left_date = date_ - timedelta(days=left_range)
        right_date = date_ + timedelta(days=right_range)

        return {"date__range" : [left_date, right_date]}
    
    @staticmethod
    def take_whole_week(date_):
        return DateFilter.around_date(date_, date_.weekday(), 6 - date_.weekday())

    @staticmethod
    def this_week():
        return DateFilter.take_whole_week(date.today())
    
    @staticmethod
    def next_week():
        return DateFilter.take_whole_week(date.today() + timedelta(weeks=1))
    

class ParticipantFilter(UtilityFilterBase):
    """Only for work with Event model fields
    """

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
    def by_repr_event_relative(cls, repr : str|list[str]):
        """Only for work with Event model fields

        Use list of places repr for OR behaviour

        repr must be in format: "{building} {room}" (separated by space)
        """

        filter_ = cls.by_repr(repr)

        for key in list(filter_.keys()):
            filter_["places_override__{}".format(key)] = filter_.pop(key)

        return filter_

    @classmethod
    def by_repr(cls, repr : str|list[str]):
        """

        Use list of places repr for OR behaviour

        repr must be in format: "{building} {room}" (separated by space)
        """

        from api.utilities import Utilities

        fitler_ = {}

        if type(repr) is list:
            buildings = []
            rooms = []
            
            for r in repr:
                building, room = Utilities.normalize_place_repr(r)

                buildings.append(building)
                rooms.append(room)

            if buildings:
                fitler_ = cls.by_building(buildings)
            fitler_.update(cls.by_room(rooms))
        else:
            building, room = Utilities.normalize_place_repr(repr)
            
            fitler_ = cls.by_building(building)
            fitler_.update(cls.by_room(room))

        return fitler_

    @staticmethod
    def by_building(building : str|list[str]):
        """

        Use list of place buildings for OR behaviour
        """

        if type(building) is list:
            return {"building__in" : building}

        return {"building" : building}

    @staticmethod
    def by_room(room : str|list[str]):
        """

        Use list of place rooms for OR behaviour
        """
        
        if type(room) is list:
            return {"room__in" : room}

        return {"room" : room}
    

class SubjectFilter(UtilityFilterBase):
    """Only for work with Event model fields
    """

    @staticmethod
    def by_name(name : str|list[str]):
        """

        Use list of subject names for OR behaviour
        """

        if type(name) is list:
            return {"subject_override__name__in" : name}

        return {"subject_override__name" : name}
    

class TimeSlotFilter(UtilityFilterBase):
    @classmethod
    def by_repr_event_relative(cls, repr : str|list[str]):
        """Only for work with Event model TimeSlot field.

        Use list of time slots repr for OR behaviour
        """

        filter_ = cls.by_repr(repr)

        for key in list(filter_.keys()):
            filter_["time_slot_override__{}".format(key)] = filter_.pop(key)

        return filter_
    
    @classmethod
    def by_repr_abstract_event_relative(cls, repr : str|list[str]):
        """Only for work with AbstractEvent model TimeSlot field.

        Use list of time slots repr for OR behaviour
        """

        filter_ = cls.by_repr(repr)

        for key in list(filter_.keys()):
            filter_["time_slot__{}".format(key)] = filter_.pop(key)

        return filter_

    @classmethod
    def by_repr(cls, repr : str|list[str]) -> dict|None:
        """Gives filter query for TimeSlot by it start_time (firstly) OR alt_name (secondly)

        Correctly works with repr in next formats:
            \d-\d for alt name
            HH:MM for start time
            HH:MM HH:MM for start and end times

        Use list of time slots repr for OR behaviour

        Returns filter query for only one of start_time OR alt_name repr (!)

        Returns None when cannot create filter query from given repr
        """

        ## TODO: remove _
        # making query from start time should be first
        # to prevent problem in some situations
        # e.g. 8:30-10.00
        filter_query_from_start_times, _ = cls.by_start_time(repr)
        
        if filter_query_from_start_times:
            return filter_query_from_start_times
        
        ## TODO: remove _
        filter_query_from_alt_names, _ = cls.by_alt_name(repr)    

        if filter_query_from_alt_names:
            return filter_query_from_alt_names
        
        return None
    
    @staticmethod
    def by_start_time(start_time : str|list[str]) -> tuple[dict, list]:
        """Makes filter query for TimeSlot using it start_time. 
        start_time must be in format: HH:MM (only colon separator acceptable)

        Use list of time slots start_time for OR behaviour

        Method can handle start_time combined with end_time ("8:30 10:00"). Result will be the same

        Returns a dict of filter queries and list of strings, that cannot be used for filtering by start_time
        """

        # 9:00
        # 13:01
        START_TIME_REG_EX = r"\d{1,2}\:{1}\d{2}"

        matches = []

        if type(start_time) is list:
            start_time_list = start_time
        else:
            start_time_list = [start_time]

        for time in list(start_time_list):
            match_ = re.search(START_TIME_REG_EX, time)

            if match_:
                matches.append(match_[0])
                start_time_list.remove(time)

        if matches:
            if len(matches) == 1:
                return {"start_time__contains" : matches[0]}, start_time_list
            
            return {"start_time__in" : matches}, start_time_list

        return {}, start_time_list

    @staticmethod
    def by_alt_name(alt_name : str|list[str]) -> tuple[dict, list]:
        """Makes filter query for TimeSlot using it alt_name

        Use list of time slots alt_names for OR behaviour

        Returns a dict of filter queries and list of strings, that cannot be used for filtering by alt_name
        """

        # 11-12
        # 10-15
        # 0-0
        # 9-8
        ALT_NAME_REG_EX = r"\d{1,2}\-+\d{1,2}"

        matches = []

        if type(alt_name) is list:
            alt_names_list = alt_name
        else:
            alt_names_list = [alt_name]

        for name in list(alt_names_list):
            match_ = re.search(ALT_NAME_REG_EX, name)

            if match_:
                matches.append(match_[0])
                alt_names_list.remove(name)

        if matches:
            if len(matches) == 1:
                return {"alt_name" : matches[0]}, alt_names_list
            
            return {"alt_name__in" : matches}, alt_names_list

        return {}, alt_names_list


class KindFilter(UtilityFilterBase):
    """Only for work with Event model fields
    """
    
    @staticmethod
    def by_name(name : str|list[str]):
        """

        Use list of subject names for OR behaviour
        """

        if type(name) is list:
            return {"kind_override__name__in" : name}

        return {"kind_override__name" : name}


class EventFilter(UtilityFilterBase):
    """Only for work with Event model fields
    """

    @staticmethod
    def overriden():
        return {"is_event_overriden" : True}
    
    @staticmethod
    def not_overriden():
        return {"is_event_overriden" : False}

    @staticmethod
    def by_schedule(schedule):
        return {"abstract_event__schedule" : schedule}

    @staticmethod
    def by_department(department):        
        return {"abstract_event__schedule__schedule_template__department" : department}
    

class AbstractEventFilter(UtilityFilterBase):
    """Only for work with AbstractEvent model fields
    """

    @staticmethod
    def with_existing_events():
        return {"pk__in" : Event.objects.values_list("abstract_event__pk", flat=True).distinct()}
