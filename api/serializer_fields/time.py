from rest_framework import serializers
from django.utils import timezone
import datetime


class TimestampField(serializers.Field):
    def to_representation(self, value):
        if value:
            return int(value.timestamp())
        return None

    def to_internal_value(self, data):
        try:
            # Преобразуем timestamp в объект datetime в UTC
            timestamp = int(data)
            return datetime.datetime.fromtimestamp(timestamp, tz=timezone.get_default_timezone())
        except (ValueError, TypeError):
            raise serializers.ValidationError("Неверный формат timestamp")
        

class TimeArrayField(serializers.Field):
    def to_representation(self, value):
        return [value.hour, value.minute]

    def to_internal_value(self, data):
        if isinstance(data, list) and len(data) == 2:
            hour, minute = data
            return datetime.time(hour=hour, minute=minute)
        elif isinstance(data, datetime.time):
            return data
        raise serializers.ValidationError("Неверный формат времени. Ожидается [часы, минуты]")

