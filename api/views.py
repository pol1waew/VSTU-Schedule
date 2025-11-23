import json

from django.shortcuts import redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from api.filters import EventFilter, ScheduleFilter
from api.importers import JSONImporter
from api.models import Event, EventKind, EventParticipant, EventPlace, Schedule, Subject
from api.serializers import (
    EventParticipantSerializer,
    EventPlaceSerializer,
    EventSerializer,
    FileUploadSerializer,
    ScheduleSerializer,
    SubjectSerializer,
)


class SchedulesAPIRootView(APIRootView):
    """
    Данное API предназначен для получения, изменения обновления информации о расписаниях ВолгГТУ
    API предоставляет базовое управления сущностями, представляющими элементы расписания

    # Общая информация
    API позволяет управлять следующими сущностями: <br>

    - [Расписание](/api/schedules)<br>
    - [Занятие](/api/events)<br>
        - [Тип занятия](/api/events/kind) (только чтение) <br>
    - [Место проведения](/api/lessonrooms)<br>
    - [Тип события](/api/events/kind)<br>
    - [Группы](/api/groups) и [преподаватели](/api/teachers)<br>


    Каждая сущность имеет вариативность действия в зависимости от метода запроса.
    Так, GET возвращает список всех сущностей, POST - добавляет новую.

    Большинство списков сущностей поддерживают опциональный аргумент `search` в URL,
    который позволяет искать записи по ключевым полям

    Более того, можно просматривать элемент каждой сущности по id. Пример URL: `/api/events/1`,
    он также поддерживает методы PUT, UPDATE, DELETE для модификации значений.


    > Возможности создания, удаления, обновления записей поддерживаются,
    > только если пользователь авторизован как администратор

    Администраторам доступны дополнительные (отладочные поля)
    в ответе для каждой записи, которые могут отсутствовать, если они равны `null`: <br>

    - `datecreated` - дата создания записи (нельзя изменить) <br>
    - `datemodified` - дата изменения записи (нельзя изменить) <br>
    - `dateaccessed` - дата последнего доступа к записи (нельзя изменить) <br>
    - `idnumber` - уникальный строковый идентификатор для отладочных целей и импорта <br>
    - `author` - автор записи (может быть программным компонентом, т.е. сервисным аккаунтом) <br>
    - `note` - комментарий для записи (максимальная длина - 1024 символа) <br>

    ## Внутренние коды ошибок


    `0` - неизвестная ошибка. Более подробную информацию нужно брать из сообщения об ошибке и кода ошибки HTTP<br>
    `1` - ошибка проверки данных. Одно из переданных значений не является валидным<br>
    `2` - ошибка доступа. Возможно, требуется авторизация или особая роль<br>
    `3` - ошибка выполнения аутентификации<br>
    `4` - нереализованная на данный момент возможность API<br>

    ## Для администраторов

    Если вы являетесь администратором, то можете [перейти в панель администратора](/admin),
    в которой доступно более детальное управление базой данных расписаний

    Сервис поддерживает импорт данных в API из сторонних источников, доступный только администраторам:<br>

    - [из JSON](/api/import/json)<br>
    - [из внешней базы данных](/api/import/db) (пока недоступно)<br>

    """

    def get_view_name(self):
        return "API Расписаний ВолгГТУ"


class EventKindListView(generics.ListAPIView):
    """
    # GET
    - Возвращает: список строк - известных типов событий <br>

    > Типы событий нельзя изменить из API, их можно только просмотреть все
    """

    queryset = EventKind.objects.all()

    def get(self, request, *args, **kwargs):
        event_kinds = EventKind.objects.values("name")
        return Response(event_kinds)

    def get_view_name(self):
        return "Типы событий"


class CommonViewSet(viewsets.ModelViewSet):
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = []

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset


class SubjectViewSet(CommonViewSet):
    """
    # GET
    - Поддерживается поиск по списку <br>
    - Возвращает список объектов - предметов <br>
    Пример формата:
    ```json
    {
        "name": "Subject", // название предмета
        "id": 3
    }
    ```
    # Аргументы, доступные для изменения <br>
    - `name` - имя (строка)
    """

    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    search_fields = ["name"]

    def get_view_name(self):
        return "Предмет"


class LessonRoomViewSet(CommonViewSet):
    """
    # GET
    - Поддерживается поиск по списку <br>
    - Возвращает список объектов - местах проведения <br>
    Пример формата:
    ```json
    {
        "building": "ГУК",
        "room": "303",
        "id": 30
    }
    ```

    # Аргументы, доступные для изменения:
    - `room` - аудитория (строка) <br>
    - `building` - корпус (строка) <br>
    """

    queryset = EventPlace.objects.all()
    serializer_class = EventPlaceSerializer
    search_fields = ["building", "room"]

    def get_view_name(self):
        return "Место проведения"


class GroupViewSet(CommonViewSet):
    """
    # GET
    - Поддерживается поиск по списку <br>
    - Возвращает список объектов - участников занятия в роли студентов (групп) <br>
    Пример формата:
    ```json
    {
        "id": 4,
        "name": "ПрИн-367"
        "role": "student",
    }
    ```

    # Аргументы, доступные для изменения: <br>
    - `name` - название группы (строка) <br>
    - `role` - значение всегда "student" <br>
    """

    queryset = EventParticipant.objects.filter(role=EventParticipant.Role.STUDENT).all()
    serializer_class = EventParticipantSerializer
    search_fields = ["name"]

    def get_view_name(self):
        return "Группа"


class TeacherViewSet(CommonViewSet):
    """
    # GET
    - Поддерживается поиск по списку <br>
    - Возвращает список объектов - участников занятия в роли студентов (групп) <br>
    Пример формата:
    ```json
    {
        "id": 7,
        "name": "Иванов Иван Иванович"
        "role": "teacher"
    }
    ```

    # Аргументы, доступные для изменения: <br>
    - `name` - название группы (строка) <br>
    - `role` - значение всегда "teacher" или "assistant" <br>
    """

    queryset = EventParticipant.objects.filter(
        role__in=[EventParticipant.Role.ASSISTANT, EventParticipant.Role.TEACHER]
    )
    serializer_class = EventParticipantSerializer
    search_fields = ["name"]

    def get_view_name(self):
        return "Преподаватель"


class EventViewSet(CommonViewSet):
    """
    # GET
    - Возвращает список объектов - занятий (событий), привязанных к расписанию <br>
    Пример формата:
    ```json
    {
        "id": 7,
        "subject": {
            "name": "Программирование",
            "id": 782
        },
        "kind": "Семинар",
        "participants": [
            {
                "name": "ПрИн-266",
                "role": "student"
            }
        ],
        "holding_info": [
            {
                "place": {
                    "building": "ГУК",
                    "room": "303",
                    "id": 30
                },
                "date": "2024-10-01"
                "time_slot": {
                    "start": [10, 10],
                    "end": [11, 40]
                }
            }
        ]
    }
    ```

    ## Аргументы GET-запроса для фильтрации списка: <br>
    - `schedule` - целое число, вывод занятий, принадлежащих заданному расписанию <br>
    - `date_from`, `date_to` - искать занятия среди дат (от и до включительно), строка даты в формате ISO-8601 <br>
    - `time_from`, `time_to` - искать занятия, проходящие в это время. Рассматривается отдельно от даты, строка времени в формате ISO-8601 <br>
    - `participants` - список ID возможных участников. Работает как фильтр, а не точный поиск по наличию всех заданных участников <br>
    - `can_have_kind` - список строк - возможных типов события.  Работает как фильтр, а не точный поиск по наличию всех заданных типов <br>
    - `possible_rooms` - список ID возможных аудиторий. Работает как фильтр, а не точный поиск по наличию всех заданных участников <br>

    # Аргументы, доступные для изменения: <br>
    - `subject` - предмет (объект, [см. предметы](/api/subjects)) (обязательный) <br>
    - `kind` - [тип события](/api/events/kind), задается строкой <br>
    - `participants` - список участников (обязательный) (см. [группу](/api/groups) или [преподавателей](/api/teachers)) <br>
    - `holding_info` - список объектов с полями (обязательный): <br>
        - `place` - [см. места проведения](/api/lessonrooms) <br>
        - `date` - дата (без времени) в формате ISO-8601 <br>
        - `time_slot` - временной интервал с временем начала и окончания. <br>
        Время представляется как массив [часы, минуты]

    > При создании записи для аргументов `subject`, объектов из списков `participants`, а также вложенных объектов `place` необходимо указывать атрибут id внутри их объекта, если нужно добавить уже существующий объект, а не создавать его заново. Если задан id, то остальное содержимое объекта игнорируется при создании записи

    """

    filterset_class = EventFilter
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def get_view_name(self):
        return "Занятие"


class ScheduleViewSet(CommonViewSet):
    """
    # GET
    - Поддерживается поиск по списку <br>
    - Возвращает список объектов - информацию о расписаниях <br>
    Пример формата:
    ```json
    {
        "faculty": "ФЭВТ",
        "scope": "bachelor",
        "course": 3,
        "semester": 1,
        "years": "2024-2025",
        "id": 5,
        "start_date": "2024-09-02", // дата первого занятия в расписании
        "end_date": "2024-12-29" // дата последнего занятия в расписании
    }
    ```

    ## Аргументы GET-запроса для фильтрации списка: <br>
    - `faculty` - строка, показать расписания принадлежащие факультету <br>
    - `scope` - строка, показать расписания соответствующие данному типу обучения (см. аргументы объекта ниже) <br>
    - `course` - целое число, номер курса <br>
    - `semester` - целое число, семестр курса <br>
    - `has_events` - список ID занятий, которые должны содержаться в найденных расписаниях (не обязательно в одном расписании). <br>


    # Аргументы доступные для изменения: <br>
    - `faculty` - факультет (строка) <br>
    - `scope` - приндлежность расписания к обучению, одно из значений: "bachelor", "master", "postgraduate", "consultation" <br>
    - `course` - целое число, номер курса <br>
    - `semester` - целое число, номер семестра <br>
    - `years` - учебный год обучения (строка, пример: 2024-2025) <br>
    """

    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    search_fields = ["faculty", "years"]
    filterset_class = ScheduleFilter

    def get_view_name(self):
        return "Расписание"


class DBImportAPIView(APIView):
    """
    Данная функциональность не реализована на текущий момент. Это заглушка.
    """

    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        # Заглушка для импорта базы данных
        return Response(
            {"type": "error", "message": "Not implemented", "error_code": 4},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )

    def get_view_name(self):
        return "Импортирование из внешней базы данных"


class JSONImportAPIView(APIView):
    """
    Данный инструмент позволяет администратору заполнять базу данных API расписаний
    с помощью укомплектованного JSON файла специального формата

    # Описание формата

    Все объекты модели (поля в таблицах) заполняются по уникальному строковому идентификатору `idnumber`,
    он может быть произвольной строкой до 255 символов, например UUID или любой другой формат уникального ID, который предпочтет администратор или система, формирующие данные для импорта в БД для API
    В будущем, по заданному строковому идентификатору можно будет выполнить редактирование записи через импорт JSON
    Не рекомендуется использовать числа в качестве строкового идентификатора. В будущем, по ним будет неудобно ориентироваться


    На данный момент формат экспорта не поддерживает опциональное указание свойств объекта из модели
    Чтобы отредакторировать запись в таблице (объект модели) необходимо указать
    все возможные поля этого объекта, а также уникальный строковый идентификатор, который был указан для этой записи заранее при предыдущих импортах или другим способом


    Содержимое JSON должно представлять собой объект, в котором есть следующие ключи со списком:

    - `subjects` - список предметов, содержащий объекты с ключом `name`, указывающим имя предмета <br>
    - `event_kinds` - список типов событий, содержащий объекты с ключом `name`, указывающим тип события <br>
    - `time_slots` - список временных интервалов, содержащий объекты с ключами `start_time`, `end_time`.
    Время указывается строкой в формате HH:MM <br>
    - `event_places` - список мест проведения событий с ключами `building`, `room` <br>
    - `event_participants` - список участников события с ключами `name`, `role` (значение перечисления, см. [в объекте преподавателя](/api/teachers) и [объекте групп обучающихся](/api/groups)) <br>
    - `schedules` - список расписаний с ключами `faculty`, `scope`, `course`, `semester`, `years` (см. в [объекте расписаний](/api/schedules)) <br>
    - `events` - список событий вместе с информацией об их проведении. Ключи `kind_id`, `schedule_id`, `subject_id` обозначают один `idnumber` соответствующих объектов (по сути, ссылка на него),
    также объект события требует наличия списка `participants`, состоящего из `idnumber` участников,
    и списка `holding_info`, который содержит объекты информации о проведении. Этот объект содержит ключ `date`, а также `place_id` и `slot_id`, являющиеся одним `idnumber` места проведения и временного интервала проведения события соответственно <br>

    Также, стоит отметить, что у всех объектов, импортируемых через JSON, должен быть уникальный строковый идентификатор, который хранится в ключе `idnumber`
    """

    permission_classes = [IsAdminUser]
    serializer_class = FileUploadSerializer

    def post(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            json_file = serializer.validated_data.get("file", None)
            if json_file:
                # Обработка файла
                file_data = json_file.read().decode("utf-8")
                json_content = json.loads(file_data)
                return self.process_content(json_content)

        json_content = json.loads(request.body.decode("utf-8"))
        return self.process_content(json_content)

    def process_content(self, json_content):
        JSONImporter(json_content).import_data()
        return Response({"result": True}, status=status.HTTP_200_OK)

    def get_view_name(self):
        return "Импортирование данных из JSON"


class ObtainAPIUserToken(ObtainAuthToken):
    """
    View для получения токена авторизации
    """

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key, "user_id": user.pk, "email": user.email, "expires": False}
        )


def index(request):
    return redirect("/visualization", False)
