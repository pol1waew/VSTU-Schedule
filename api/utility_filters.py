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

        for key in filter_.keys():
            filter_["places_override__{}".format(key)] = filter_.pop(key)

        return filter_

    @classmethod
    def by_repr(cls, repr : str|list[str]):
        """

        Use list of places repr for OR behaviour

        repr must be in format: "{building} {room}" (separated by space)
        """

        fitler_ = {}

        if type(repr) is list:
            building = []
            room = []
            
            for r in repr:
                building.append(r.split(" ", 1)[0])
                room.append(r.split(" ", 1)[1])

            fitler_ = cls.by_building(building)
            fitler_.update(cls.by_room(room))
        else:
            print(repr)
            fitler_ = cls.by_building(repr.split(" ", 1)[0])
            fitler_.update(cls.by_room(repr.split(" ", 1)[1]))

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
        """Only for work with Event model fields

        Use list of time slots repr for OR behaviour
        """

        filter_ = cls.by_repr(repr)

        for key in filter_.keys():
            filter_["time_slot_override__{}".format(key)] = filter_.pop(key)

        return filter_

    @staticmethod
    def by_repr(repr : str|list[str]):
        """

        Use list of time slots repr for OR behaviour
        """

        REG_EX = r"\d{1,2}\D+\d{1,2}"

        if type(repr) is list:
            alt_names = []
        
            for r in repr:
                alt_names.append(re.search(REG_EX, r)[0])

            return {"alt_name__in" : alt_names}

        return {"alt_name" : re.search(REG_EX, repr)[0]}
    

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

class ScheduleFilter(UtilityFilterBase):
    """Only for work with Schedule model fields
    """
    
    @staticmethod
    def by_base_parameters(course : int, 
                           faculty : str,
                           semester : int,
                           years : str):
        """

        Years must be presented in format: YYYY-YYYY (START_YEAR-END_YEAR)
        """
        
        return {"metadata__course" : course,
                "schedule_template__metadata__faculty" : faculty,
                "metadata__semester" : semester,
                "metadata__years" : years}
