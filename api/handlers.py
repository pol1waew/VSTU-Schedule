import traceback
from django.conf import settings
from rest_framework.renderers import JSONRenderer
from rest_framework.exceptions import (
    ValidationError,
    NotAuthenticated,
    PermissionDenied,
    AuthenticationFailed,
)
from rest_framework.views import exception_handler

from api.exceptions import ScheduleAPIException


class ResponseJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context and renderer_context.get("response", None):
            response = renderer_context["response"]
            if response.status_code >= 400:
                return super().render(data, accepted_media_type, renderer_context)

        response_data = {
            "type": "response",
            "items": data if isinstance(data, list) else [data],
        }

        return super().render(response_data, accepted_media_type, renderer_context)


def exception_response_handler(exc, context):
    response = exception_handler(exc, context)

    if settings.DEBUG:
        traceback.print_exc()

    if response is not None:
        # Определяем тип ошибки и сообщение
        detail_message = None
        if isinstance(response.data, dict):
            detail_message = response.data.get("detail")
        response.data = {"type": "error", "message": detail_message}
        add_exception_data_to_response(response, exc)
        if settings.DEBUG:
            response.data["exception_class"] = type(exc).__qualname__

    return response


def add_exception_data_to_response(response, exception):
    # TODO: Нужно более детерминированное опознание ошибок и выдачи их информации

    if isinstance(exception, ScheduleAPIException):
        error_code = exception.internal_error_code
    elif isinstance(exception, ValidationError):
        error_code = 1
        response.data["message"] = "Введены некорректные данные"
        response.data["validation_details"] = exception.detail
    elif isinstance(exception, NotAuthenticated | PermissionDenied):
        error_code = 2
        response.data["message"] = "У вас нет прав для выполнения данного запроса"
    elif isinstance(exception, AuthenticationFailed):
        error_code = 3
        response.data["message"] = "Не удалось произвести авторизацию"
    elif isinstance(exception, NotImplementedError):
        error_code = 4
        response.data["message"] = "Данная функциональность пока не реализована"
    else:
        error_code = 0
    response.data["error_code"] = error_code

    if not response.data["message"] and hasattr(exception, "message"):
        # Пробуем вывести сообщение об ошибке прямо из исключения
        response.data["message"] = exception.message
    elif not response.data["message"]:
        response.data["message"] = (
            "Неизвестная ошибка. Обратитесь к коду ошибки HTTP, логам приложения"
        )