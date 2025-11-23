import json
from api.utilities import Utilities
from rest_framework.exceptions import ValidationError
from api.models import (
    EventPlace,
    Event,
    EventKind,
    EventParticipant,
    Schedule,
    Subject,
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

        EventPlace.objects.bulk_create(places_to_create)

    @staticmethod
    def import_participant_reference():
        pass
