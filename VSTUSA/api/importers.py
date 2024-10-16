from rest_framework.exceptions import ValidationError

from api.models import (
    Event,
    EventHolding,
    EventKind,
    EventParticipant,
    EventPlace,
    Schedule,
    Subject,
    TimeSlot,
)


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
        event_holdings = []
        for item in data.get("events", []):
            self._check_idnumber(item)
            event = Event(
                idnumber=item["idnumber"],
                subject=Subject.objects.get(idnumber=item["subject_id"]),
                kind=EventKind.objects.get(idnumber=item["kind_id"]),
                schedule=Schedule.objects.get(idnumber=item["schedule_id"]),
            )
            events.append(event)

            # Загрузка EventHoldings
            for holding_item in item.get("holding_info", []):
                self._check_idnumber(holding_item)
                event_holdings.append(
                    EventHolding(
                        idnumber=holding_item["idnumber"],
                        place=EventPlace.objects.get(idnumber=holding_item["place_id"]),
                        date=holding_item["date"],
                        time_slot=TimeSlot.objects.get(idnumber=holding_item["slot_id"]),
                        event=event,
                    )
                )

        Event.objects.bulk_create(
            events,
            update_conflicts=True,
            unique_fields=["idnumber"],
            update_fields=["subject", "kind", "schedule"],
        )
        EventHolding.objects.bulk_create(
            event_holdings,
            update_conflicts=True,
            unique_fields=["idnumber"],
            update_fields=["place", "date", "time_slot"],
        )
