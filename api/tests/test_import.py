from datetime import datetime
from django.test import TestCase
from api.utilities import ImportAPI
from api.models import (
    Schedule,
    ScheduleTemplate,
    ScheduleMetadata,
    ScheduleTemplateMetadata,
    EventParticipant,
    Department,
    Organization,
    AbstractDay,
    TimeSlot
)

class TestImportAPI(TestCase):
    TEST_JSON = """
    {
        "title": "Учебные занятия 4 курса ФЭВТ на 2 семестр 2024-2025 учебного года",
        "table": {
            "grid": [
                {
                    "subject": "ВКР",
                    "kind": "лекция",
                    "participants": {
                        "teachers": [
                            "Гилка В.В.",
                            "Кузнецова А.С."
                        ],
                        "student_groups": [
                            "ИВТ-460"
                        ]
                    },
                    "places": [
                        "В 902а",
                        "В 902б"
                    ],
                    "hours": [
                        "1-2",
                        "3-4"
                    ],
                    "week_day_index": 0,
                    "week": "first_week",
                    "holds_on_date": [
                        "09.11.2024"
                    ]
                },
                {
                    "subject": "МИКРОПРОЦЕССОРЫ",
                    "kind": "лабораторная работа",
                    "participants": {
                        "teachers": [
                            "Синкевич Д.",
                            "Дмитриев А.С."
                        ],
                        "student_groups": [
                            "ПрИн-466",
                            "ПрИн-467"
                        ]
                    },
                    "places": [
                        "В 903",
                        "В 908"
                    ],
                    "hours": [
                        "5-6",
                        "7-8"
                    ],
                    "week_day_index": 1,
                    "week": "second_week",
                    "holds_on_date": []
                }
            ],
            "datetime": {
                "weeks": {
                    "first_week": [
                        {
                            "week_day_index": 0,
                            "calendar": [
                                {
                                    "month_index": 0,
                                    "month_days": [
                                        "1", 
                                        "15"
                                    ]
                                },
                                {
                                    "month_index": 1,
                                    "month_days": [
                                        "20", 
                                        "28"
                                    ]
                                }
                            ]
                        }
                    ],
                    "second_week": [
                        {
                            "week_day_index": 0,
                            "calendar": [
                                {
                                    "month_index": 0,
                                    "month_days": [
                                        "8", 
                                        "22"
                                    ]
                                }
                            ]
                        },
                        {
                            "week_day_index": 1,
                            "calendar": [
                                {
                                    "month_index": 0,
                                    "month_days": [
                                        "9", 
                                        "23"
                                    ]
                                }
                            ]
                        }
                    ]
                },
                "week_days": [
                    "ПОНЕДЕЛЬНИК",
                    "ВТОРНИК",
                    "СРЕДА",
                    "ЧЕТВЕРГ",
                    "ПЯТНИЦА",
                    "СУББОТА"
                ],
                "months": [
                    "февраль",
                    "март",
                    "апрель",
                    "май",
                    "июнь",
                    "сентябрь"
                ]
            }
        }
    }

    """

    def setUp(self):
        self.create_abstract_days()
        self.create_time_slots()
        self.create_schedule()

    def create_abstract_days(self):
        AbstractDay.objects.bulk_create([
            AbstractDay(day_number=0, name="1 неделя, Понедельник"),
            AbstractDay(day_number=1, name="1 неделя, Вторник"),
            AbstractDay(day_number=2, name="1 неделя, Среда"),
            AbstractDay(day_number=3, name="1 неделя, Четверг"),
            AbstractDay(day_number=4, name="1 неделя, Пятница"),
            AbstractDay(day_number=5, name="1 неделя, Суббота"),
            AbstractDay(day_number=6, name="1 неделя, Воскресенье"),
            AbstractDay(day_number=7, name="2 неделя, Понедельник"),
            AbstractDay(day_number=8, name="2 неделя, Вторник"),
            AbstractDay(day_number=9, name="2 неделя, Среда"),
            AbstractDay(day_number=10, name="2 неделя, Четверг"),
            AbstractDay(day_number=11, name="2 неделя, Пятница"),
            AbstractDay(day_number=12, name="2 неделя, Суббота"),
            AbstractDay(day_number=13, name="2 неделя, Воскресенье")
        ])

    def create_time_slots(self):
        TimeSlot.objects.bulk_create([
                TimeSlot(alt_name="1-2", start_time=datetime.strptime("08:30:00", "%H:%M:%S"), end_time=datetime.strptime("10:00:00", "%H:%M:%S")),
                TimeSlot(alt_name="3-4", start_time=datetime.strptime("10:10:00", "%H:%M:%S"), end_time=datetime.strptime("11:40:00", "%H:%M:%S")),
                TimeSlot(alt_name="5-6", start_time=datetime.strptime("11:50:00", "%H:%M:%S"), end_time=datetime.strptime("13:20:00", "%H:%M:%S")),
                TimeSlot(alt_name="7-8", start_time=datetime.strptime("13:40:00", "%H:%M:%S"), end_time=datetime.strptime("15:10:00", "%H:%M:%S")),
                TimeSlot(alt_name="9-10", start_time=datetime.strptime("15:20:00", "%H:%M:%S"), end_time=datetime.strptime("16:50:00", "%H:%M:%S")),
                TimeSlot(alt_name="11-12", start_time=datetime.strptime("17:00:00", "%H:%M:%S"), end_time=datetime.strptime("18:30:00", "%H:%M:%S"))
        ])

    def create_schedule(self):
        organization_ = Organization.objects.create(
            name="ВолГТУ"
        )
        
        department_ = Department.objects.create(
            name="ФЭВТ",
            organization=organization_
        )

        schedule_template_metadata = ScheduleTemplateMetadata.objects.create(
            faculty="ФЭВТ",
            scope=ScheduleTemplateMetadata.Scope.BACHELOR
        )

        schedule_template = ScheduleTemplate.objects.create(
            metadata=schedule_template_metadata,
            repetition_period=14,
            repeatable=True,
            aligned_by_week_day=1,
            department=department_
        )

        schedule_metadata = ScheduleMetadata.objects.create(
            years="2024-2025",
            course=4,
            semester=2
        )
        
        Schedule.objects.create(
            metadata=schedule_metadata,
            status=Schedule.Status.ACTIVE,
            start_date=datetime.strptime("01.09.2025", "%d.%m.%Y"),
            end_date=datetime.strptime("01.02.2026", "%d.%m.%Y"),
            starting_day_number=AbstractDay.objects.get(day_number=0),
            schedule_template=schedule_template
        )
        
    def test_test(self):
        ImportAPI.import_data(self.TEST_JSON)

        try:
            gilka = EventParticipant.objects.get(name="Гилка В.В.")
        except EventParticipant.DoesNotExist:
            gilka = None

        self.assertNotEqual(gilka, None)
