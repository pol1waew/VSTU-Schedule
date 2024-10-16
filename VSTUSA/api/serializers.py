from django.db.models import ForeignKey, ManyToManyField
from rest_framework import serializers

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
from api.serializer_fields.time import TimeArrayField, TimestampField


class CommonModelSerializer(serializers.ModelSerializer):
    admin_readonly_fields = {
        "datecreated": TimestampField(),
        "datemodified": TimestampField(),
        "dateaccessed": TimestampField(allow_null=True),
    }
    admin_fields = {
        "idnumber": serializers.CharField(allow_null=True),
        "note": serializers.CharField(allow_blank=True, allow_null=True, max_length=1024),
        "author": serializers.CharField(allow_null=True),
    }
    visible_nullable = []  # nullable поля, которые нужно обязательно выводить всегда, даже если они равны

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")

        if request and request.user.is_staff:
            for field in self.admin_readonly_fields:
                value = getattr(instance, field)
                if value is None:
                    representation[field] = None
                else:
                    representation[field] = self.admin_readonly_fields[field].to_representation(
                        value
                    )
            for field in self.admin_fields:
                value = getattr(instance, field)
                if value is None:
                    representation[field] = None
                else:
                    representation[field] = self.admin_fields[field].to_representation(value)

        # убираем из вывода ненужные null поля
        return {
            key: value
            for key, value in representation.items()
            if value is not None or value in self.visible_nullable
        }

    def _detect_record_update(self, instance, validated_data):
        request = self.context.get("request")

        if request and request.user.is_staff:
            for field in self.admin_fields:
                if field in validated_data and field in self.admin_fields:
                    validated_data[field] = self.admin_fields[field].to_internal_value(
                        validated_data[field]
                    )
                    setattr(instance, field, validated_data[field])

    def update(self, instance, validated_data):
        self._detect_record_update(instance, validated_data)
        return super().update(instance, validated_data)


class CommonModelListSerializer(serializers.ListSerializer):
    """
    Подробнее о необходимости внедрения этого класса читать здесь:
    https://www.django-rest-framework.org/api-guide/serializers/#deserializing-multiple-objects
    https://www.django-rest-framework.org/api-guide/serializers/#customizing-multiple-update
    """

    def update(self, instance, validated_data):
        instance = instance.all()
        instance_mapping = {obj.id: obj for obj in instance}
        new_data = [
            validated_data[i]
            for i in range(len(validated_data))
            if validated_data[i].get("id") is None
        ]
        for data in new_data:
            validated_data.remove(data)
        data_mapping = {item["id"]: item for item in validated_data}

        # Обновляем или создаем объекты
        ret = []
        for obj_id, data in data_mapping.items():
            if obj_id in instance_mapping:
                # Обновление существующего объекта
                obj = instance_mapping[obj_id]
                ret.append(self.child.update(obj, data))
            else:
                # Создание нового объекта
                ret.append(self.child.create(data))
        for data in new_data:
            ret.append(self.child.create(data))

        for ins_id, ins in instance_mapping.items():
            if ins_id not in data_mapping:
                self._remove_relationships(ins)

        return ret

    def _remove_relationships(self, obj):
        for field in obj._meta.get_fields():
            if isinstance(field, (ForeignKey, ManyToManyField)):
                related_manager = getattr(obj, field.name)

                if isinstance(field, ManyToManyField):
                    related_manager.clear()
                elif isinstance(field, ForeignKey):
                    if field.null:
                        setattr(obj, field.name, None)
                        obj.save()


class SubjectSerializer(CommonModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name"]
        list_serializer_class = CommonModelListSerializer


class TimeSlotSerializer(CommonModelSerializer):
    start_time = TimeArrayField(label="Время начала")
    end_time = TimeArrayField(required=False, allow_null=True, label="Время окончания")

    class Meta:
        model = TimeSlot
        fields = ["start_time", "end_time"]
        list_serializer_class = CommonModelListSerializer


class EventParticipantSerializer(CommonModelSerializer):
    class Meta:
        model = EventParticipant
        fields = ["id", "name", "role"]
        list_serializer_class = CommonModelListSerializer


class EventPlaceSerializer(CommonModelSerializer):
    class Meta:
        model = EventPlace
        fields = ["id", "building", "room"]
        list_serializer_class = CommonModelListSerializer


class EventHoldingSerializer(CommonModelSerializer):
    place = EventPlaceSerializer(label="Место")
    time_slot = TimeSlotSerializer(label="Временной интервал")
    date = serializers.DateField(format="iso-8601", label="Дата")

    class Meta:
        model = EventHolding
        fields = ["place", "date", "time_slot"]
        list_serializer_class = CommonModelListSerializer

    # DRF возлагает создание и обновление объектов из вложенных сериализаторов на разработчика!
    def create(self, validated_data):
        place_data = validated_data.pop("place", {})
        time_slot_data = validated_data.pop("time_slot", {})

        # Используем вложенные сериализаторы для создания объектов
        # DRF возлагает создание объектов из вложенных сериализаторов на разработчика!
        place_id = place_data.pop("id", None)
        place_instance = EventPlace.objects.get(id=place_id) if place_id else None

        place_serializer = EventPlaceSerializer(instance=place_instance, data=place_data)
        place_serializer.is_valid(raise_exception=True)
        place = place_serializer.save()

        timeslot_instance = TimeSlot.objects.filter(**time_slot_data).first()

        time_slot_serializer = TimeSlotSerializer(instance=timeslot_instance, data=time_slot_data)
        time_slot_serializer.is_valid(raise_exception=True)
        time_slot = time_slot_serializer.save()

        event_holding = EventHolding.objects.create(
            place=place, time_slot=time_slot, **validated_data
        )

        return event_holding

    def update(self, instance, validated_data):
        place_data = validated_data.pop("place", None)
        time_slot_data = validated_data.pop("time_slot", None)

        if place_data:
            place_data.pop("id", None)
            place_serializer = EventPlaceSerializer(
                instance.place,
                data=place_data,
            )
            place_serializer.is_valid(raise_exception=True)
            place_serializer.save()

        if time_slot_data:
            time_slot_serializer = TimeSlotSerializer(instance.time_slot, data=time_slot_data)
            time_slot_serializer.is_valid(raise_exception=True)
            time_slot_serializer.save()

        instance.date = validated_data.get("date", instance.date)
        self._detect_record_update(instance, validated_data)
        instance.save()

        return instance


class EventSerializer(CommonModelSerializer):
    participants = EventParticipantSerializer(many=True, label="Участники")
    subject = SubjectSerializer(label="Предмет")
    kind = serializers.CharField(source="kind.name", label="Тип события")
    holding_info = EventHoldingSerializer(
        source="holdings", many=True, label="Информация о проведении"
    )
    schedule_id = serializers.PrimaryKeyRelatedField(
        source="schedule", label="Расписание", queryset=Schedule.objects.all()
    )

    class Meta:
        model = Event
        fields = [
            "id",
            "kind",
            "participants",
            "subject",
            "holding_info",
            "schedule_id",
        ]
        list_serializer_class = CommonModelListSerializer

    # DRF возлагает создание и обновление объектов из вложенных сериализаторов на разработчика!
    def create(self, validated_data):
        participants_data = validated_data.pop("participants")
        subject_data = validated_data.pop("subject")
        holding_info_data = validated_data.pop("holdings")
        kind = validated_data.pop("kind")

        participants_serializer = EventParticipantSerializer(
            EventParticipant.objects.all(), data=participants_data, many=True
        )
        participants_serializer.is_valid(raise_exception=True)
        participants = participants_serializer.save()

        subject_id = subject_data.pop("id", None)
        subject_instance = Subject.objects.get(id=subject_id) if subject_id else None
        subject_serializer = SubjectSerializer(instance=subject_instance, data=subject_data)
        subject_serializer.is_valid(raise_exception=True)
        subject = subject_serializer.save()

        holding_info_serializer = EventHoldingSerializer(
            EventHolding.objects.all(), data=holding_info_data, many=True
        )
        holding_info_serializer.is_valid(raise_exception=True)
        holding_info = holding_info_serializer.save()

        kind_model = EventKind.objects.get_or_create(name=kind.get("name"))[0]

        event = Event.objects.create(
            kind=kind_model,
            subject=subject,
            **validated_data,
        )

        event.participants.set(participants)
        event.holdings.set(holding_info)

        return event

    def update(self, instance, validated_data):
        participants_data = validated_data.pop("participants", None)
        subject_data = validated_data.pop("subject", None)
        holding_info_data = validated_data.pop("holdings", None)
        kind_data = validated_data.pop("kind", None)

        if participants_data:
            participants_serializer = EventParticipantSerializer(
                instance.participants, data=participants_data, many=True
            )
            participants_serializer.is_valid(raise_exception=True)
            participants = participants_serializer.save()
            instance.participants.set(participants)

        if subject_data:
            subject_serializer = SubjectSerializer(instance.subject, data=subject_data)
            subject_serializer.is_valid(raise_exception=True)
            instance.subject = subject_serializer.save()

        if holding_info_data:
            holding_info_serializer = EventHoldingSerializer(
                instance.holdings, data=holding_info_data, many=True
            )
            holding_info_serializer.is_valid(raise_exception=True)
            holding_info = holding_info_serializer.save()
            instance.holdings.set(holding_info)

        if kind_data:
            kind_model, _ = EventKind.objects.get_or_create(name=kind_data.get("name"))
            instance.kind = kind_model

        self._detect_record_update(instance, validated_data)
        instance.schedule = validated_data.get("schedule", instance.schedule)
        instance.save()

        return instance


class ScheduleSerializer(CommonModelSerializer):
    start_date = serializers.SerializerMethodField(label="Дата начала занятий")
    finish_date = serializers.SerializerMethodField(label="Дата окончания занятий")

    class Meta:
        model = Schedule
        fields = [
            "id",
            "faculty",
            "scope",
            "course",
            "years",
            "semester",
            "start_date",
            "finish_date",
        ]
        list_serializer_class = CommonModelListSerializer

    def get_start_date(self, instance):
        return instance.first_event().min_date

    def get_finish_date(self, instance):
        return instance.last_event().max_date


class FileUploadSerializer(serializers.Serializer):
    """Необходимый для работы импорта сериализатор"""

    file = serializers.FileField(required=False)