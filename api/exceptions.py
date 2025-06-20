from rest_framework.exceptions import APIException


class ScheduleAPIException(APIException):
    internal_error_code: int = 0
    http_code: int = 500
