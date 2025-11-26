from datetime import datetime
from django.test import TestCase
from api.importers import EventImporter, ReferenceImporter
from api.utilities import EventImportAPI
from api.utility_filters import TimeSlotFilter, PlaceFilter
from api.models import (
    Schedule,
    ScheduleTemplate,
    ScheduleMetadata,
    ScheduleTemplateMetadata,
    EventParticipant,
    Department,
    Organization,
    AbstractDay,
    TimeSlot,
    AbstractEvent,
    Event,
    EventPlace,
    Subject
)

"""py manage.py test api.tests.test_import
"""

class TestEventImporter(TestCase):   
    def setUp(self):
        self.create_abstract_days()
        #self.create_time_slots()
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
        
    def test_import_data(self):
        # manualy created TimeSlot
        TimeSlot.objects.create(alt_name="11-12", start_time=datetime.strptime("17:00:00", "%H:%M:%S"), end_time=datetime.strptime("18:30:00", "%H:%M:%S"))

        with open("testdata/test_import_1.json", "r", encoding="utf8") as data_file:
            EventImportAPI.import_event_data(data_file.read())

        try:
            self.assertNotEqual(Event.objects.filter(**TimeSlotFilter.by_repr_event_relative("11-12")).first(), None)
            self.assertNotEqual(Event.objects.filter(**TimeSlotFilter.by_repr_event_relative("11:50")).first(), None)
            self.assertNotEqual(Event.objects.filter(**TimeSlotFilter.by_repr_event_relative("17:00")).first(), None)
        except Event.DoesNotExist:
            self.fail()

        try:
            self.assertNotEqual(AbstractEvent.objects.filter(**TimeSlotFilter.by_repr_abstract_event_relative("11-12")).first(), None)
            self.assertNotEqual(AbstractEvent.objects.filter(**TimeSlotFilter.by_repr_abstract_event_relative("11:50")).first(), None)
            self.assertNotEqual(AbstractEvent.objects.filter(**TimeSlotFilter.by_repr_abstract_event_relative("17:00")).first(), None)
            self.assertNotEqual(AbstractEvent.objects.filter(participants__name="Гилка В.В.").first(), None)
            self.assertNotEqual(AbstractEvent.objects.filter(participants__name="ИВТ-460", participants__role="student").first(), None)
        except AbstractEvent.DoesNotExist:
            self.fail()

        try:
            self.assertNotEqual(TimeSlot.objects.get(**TimeSlotFilter.by_start_time("17:00")[0]), None)
            self.assertNotEqual(TimeSlot.objects.get(**TimeSlotFilter.by_start_time("10:10")[0]), None)
        except TimeSlot.DoesNotExist:
            self.fail()

        try:
            self.assertNotEqual(EventPlace.objects.get(**PlaceFilter.by_repr("В 902а")), None)
        except EventPlace.DoesNotExist:
            self.fail()
    
    def test_collect_reference_data(self):
        INPUT_DATA = [
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
					"ГУК101",
					"312"
				],
				"hours": [
					"18.30",
					"11:11 -  12.01"
				],
				"week_day_index": 1,
				"week": "second_week",
				"holds_on_date": []
			}
        ]

        return_value = EventImportAPI._collect_reference_data(INPUT_DATA)
        
        self.assertSequenceEqual(
            return_value,
            {
                "subjects" : {"ВКР", "МИКРОПРОЦЕССОРЫ"},
                "kinds" : {"Лекция", "Лабораторная работа"},
                "teacher_names" : {"Гилка В.В.", "Кузнецова А.С.", "Синкевич Д.", "Дмитриев А.С."},
                "group_names" : {"ИВТ-460", "ПрИн-466", "ПрИн-467"},
                "places" : {("В", "902а"), ("В", "902б"), ("", "ГУК101"), ("", "312")},
                "time_slots" : {("1-2", "", ""), ("3-4", "", ""), ("", "18:30", ""), ("", "11:11", "12:01")}
            }
        )

    def test_ensure_reference_data(self):
        INPUT_DATA = {
            "subjects" : set(),
            "kinds" : set(),
            "teacher_names" : set(),
            "group_names" : set(),
            "places" : set(),
            "time_slots" : {
                ("1-2", "8:30", ""),
                ("", "11:55", ""),
                ("5-6", "13:40", "15:01"),
                ("", "15:09", "15:10")
            }
        }

        EventImportAPI._ensure_reference_data(INPUT_DATA)

        try:
            self.assertNotEqual(TimeSlot.objects.get(start_time__contains="8:30"), None)
            self.assertNotEqual(TimeSlot.objects.get(start_time__contains="11:55"), None)
            self.assertNotEqual(TimeSlot.objects.get(end_time__contains="15:01"), None)
            self.assertNotEqual(TimeSlot.objects.get(end_time__contains="15:10"), None)
        except TimeSlot.DoesNotExist:
            self.fail()


class TestReferenceImporter(TestCase):
    def test_place_import_reference(self):
        PLACE_REFERENCE_DATA = """
            {
                "places": [
                    "002",
                    "КЦ УНЦ",
                    "В-1402-3",
                    "Б-205а",
                    "ГУК101"
                ]
            }
        """

        ReferenceImporter.import_place_reference(PLACE_REFERENCE_DATA)

        try:
            self.assertNotEqual(EventPlace.objects.get(**PlaceFilter.by_repr("002")), None)
            self.assertNotEqual(EventPlace.objects.get(**PlaceFilter.by_repr("КЦ УНЦ")), None)
            self.assertNotEqual(EventPlace.objects.get(**PlaceFilter.by_repr("В-1402-3")), None)
            self.assertNotEqual(EventPlace.objects.get(**PlaceFilter.by_repr("Б-205а")), None)
            self.assertNotEqual(EventPlace.objects.get(**PlaceFilter.by_repr("ГУК101")), None)
        except EventPlace.DoesNotExist:
            self.fail()

    def test_import_same_place_reference(self):
        PLACE_REFERENCE_DATA = """
            {
                "places": [
                    "В-902а",
                    "В 902а",
                    "В,902а"
                ]
            }
        """

        ReferenceImporter.import_place_reference(PLACE_REFERENCE_DATA)

        try:
            self.assertEqual(EventPlace.objects.all().count(), 1)
            self.assertNotEqual(EventPlace.objects.get(building="В", room="902а"), None)
        except EventPlace.DoesNotExist:
            self.fail()

    def test_faculty_import_reference(self):
        FACULTY_REFERENCE_DATA = """
            [
                {
                    "faculty_id" : "0",
                    "faculty_fullname" : "Информационно-библиотечный центр",
                    "faculty_code" : "0000",
                    "faculty_shortname" : "ИБЦ"
                },
                {
                    "faculty_id" : "1",
                    "faculty_fullname" : "Факультет автоматизированных систем, транспорта и вооружений",
                    "faculty_code" : "0001",
                    "faculty_shortname" : "ФАСТиВ"
                },
                {
                    "faculty_id" : "2",
                    "faculty_fullname" : "Факультет автомобильного транспорта",
                    "faculty_code" : "0002",
                    "faculty_shortname" : "ФАТ"
                }
            ]
        """

        Organization.objects.create(name="ВолгГТУ")

        ReferenceImporter.import_faculty_reference(FACULTY_REFERENCE_DATA)

        try:
            self.assertEqual(Department.objects.all().count(), 3)
            self.assertEqual(Department.objects.filter(parent_department__isnull=True).count(), 3)
            self.assertNotEqual(Department.objects.get(shortname="ФАСТиВ"), None)
            self.assertNotEqual(Department.objects.get(code="2"), None)
        except Department.DoesNotExist:
            self.fail()

    def test_department_import_reference(self):
        FACULTY_REFERENCE_DATA = """
            [
                {
                    "faculty_id" : "111",
                    "faculty_fullname" : "Факультет электроники и вычислительной техники",
                    "faculty_code" : "000000111",
                    "faculty_shortname" : "ФЭВТ"
                },
                {
                    "faculty_id" : "222",
                    "faculty_fullname" : "Химико-технологический факультет",
                    "faculty_code" : "000000222",
                    "faculty_shortname" : "ХТФ"
                }
            ]
        """
        DEPARTMENT_REFERENCE_DATA = """
            [
                {
                    "department_id" : "0",
                    "department_code" : "000000000",
                    "department_fullname" : "Кафедра Автоматизация производственных процессов",
                    "department_shortname" : "АПП",
                    "faculty_id" : "111",
                    "faculty_shortname" : "ФЭВТ"
                },
                {
                    "department_id" : "1",
                    "department_code" : "000000001",
                    "department_fullname" : "Кафедра Автоматические установки",
                    "department_shortname" : "АУ",
                    "faculty_id" : "333",
                    "faculty_shortname" : "ТАКОГО ФАКУЛЬТЕТА НЕТ"
                }
            ]
        """

        Organization.objects.create(name="ВолгГТУ")

        ReferenceImporter.import_faculty_reference(FACULTY_REFERENCE_DATA)
        ReferenceImporter.import_department_reference(DEPARTMENT_REFERENCE_DATA)

        try:
            self.assertEqual(Department.objects.filter(parent_department__isnull=True).count(), 3) # 2 faculty + 1 department
            self.assertNotEqual(Department.objects.get(shortname="ФЭВТ"), None)
            self.assertNotEqual(Department.objects.get(parent_department__code="111"), None)
            self.assertEqual(Department.objects.get(code="000000001").name, "Кафедра Автоматические установки")
        except Department.DoesNotExist:
            self.fail()

    def test_subject_import_reference(self):
        SUBJECT_REFERENCE_DATA = """
        [
            {
                "discipline_code" : "000006700",
                "discipline_name" : "Динамика и устойчивость самоходного артиллерийского орудия",
                "discipline_shortname" : "ДИУСАО",
                "is_elective" : "Нет",
                "discipline_department_code" : "000000130",
                "discipline_department_id" : "2",
                "discipline_department_shortname" : "АУ"
            },
            {
                "discipline_code" : "000002373",
                "discipline_name" : "Основы проектирования WEB-приложений",
                "discipline_shortname" : "ОПW",
                "is_elective" : "Нет",
                "discipline_department_code" : "000000215",
                "discipline_department_id" : "210",
                "discipline_department_shortname" : "ВИТ"
            },
            {
                "discipline_code" : "000006579",
                "discipline_name" : "Экзамен по ПМ.05 'Организация деятельности подчиненного персонала'",
                "discipline_shortname" : "ЭПП'ДПП",
                "is_elective" : "Нет",
                "discipline_department_code" : "000000327",
                "discipline_department_id" : "329",
                "discipline_department_shortname" : "ТМ (КТИ)"
            }
        ]
        """

        ReferenceImporter.import_subject_reference(SUBJECT_REFERENCE_DATA)

        try:
            self.assertEqual(Subject.objects.all().count(), 3)
            self.assertNotEqual(Subject.objects.get(name="Основы проектирования WEB-приложений"), None)
            self.assertNotEqual(Subject.objects.get(name="Экзамен по ПМ.05 'Организация деятельности подчиненного персонала'"), None)
        except Subject.DoesNotExist:
            self.fail()

    def test_teacher_import_reference(self):
        FACULTY_REFERENCE_DATA = """
            [
                {
                    "faculty_id" : "111",
                    "faculty_fullname" : "Факультет электроники и вычислительной техники",
                    "faculty_code" : "000000111",
                    "faculty_shortname" : "ФЭВТ"
                },
                {
                    "faculty_id" : "222",
                    "faculty_fullname" : "Химико-технологический факультет",
                    "faculty_code" : "000000222",
                    "faculty_shortname" : "ХТФ"
                }
            ]
        """
        TEACHER_REFERENCE_DATA = """
        [
            {
                "staff_department_code" : "111",
                "staff_department" : "Факультет электроники и вычислительной техники",
                "staff_code" : "000008945",
                "staff_surname" : "Рамасуббу",
                "staff_name" : "Сундер",
                "staff_patronymic" : ""
            },
            {
                "staff_department_code" : "222",
                "staff_department" : "Химико-технологический факультет",
                "staff_code" : "000008785",
                "staff_surname" : "Завьялов",
                "staff_name" : "Дмитрий",
                "staff_patronymic" : "Викторович"
            }
        ]
        """
        
        Organization.objects.create(name="ВолгГТУ")

        ReferenceImporter.import_faculty_reference(FACULTY_REFERENCE_DATA)
        ReferenceImporter.import_teacher_reference(TEACHER_REFERENCE_DATA)

        try:
            self.assertEqual(EventParticipant.objects.all().count(), 2)
            self.assertNotEqual(EventParticipant.objects.get(name="Рамасуббу С."), None)
            self.assertEqual(EventParticipant.objects.get(role=EventParticipant.Role.TEACHER, department__code="222").name, "Завьялов Д.В.")
        except EventParticipant.DoesNotExist:
            self.fail()

    def test_student_import_reference(self):
        FACULTY_REFERENCE_DATA = """
            [
                {
                    "faculty_id" : "111",
                    "faculty_fullname" : "Факультет электроники и вычислительной техники",
                    "faculty_code" : "000000111",
                    "faculty_shortname" : "ФЭВТ"
                }
            ]
        """
        DEPARTMENT_REFERENCE_DATA = """
            [
                {
                    "department_id" : "1",
                    "department_code" : "000000001",
                    "department_fullname" : "Кафедра Автоматизация производственных процессов",
                    "department_shortname" : "АПП",
                    "faculty_id" : "111",
                    "faculty_shortname" : "ФЭВТ"
                },
                {
                    "department_id" : "2",
                    "department_code" : "000000002",
                    "department_fullname" : "Кафедра Автоматические установки",
                    "department_shortname" : "АУ",
                    "faculty_id" : "111",
                    "faculty_shortname" : "ФЭВТ"
                }
            ]
        """
        STUDENT_REFERENCE_DATA = """
        [
            {
                "group_code" : "000003049",
                "group_name" : "АДП-222",
                "faculty_id" : "000000001",
                "speciality" : "Управление в технических системах",
                "profile" : "Автоматизированные системы управления в цифровом производстве",
                "qualification" : "Бакалавр",
                "graduating_department_name" : ""
            },
            {
                "group_code" : "000000700",
                "group_name" : "АДП-322",
                "faculty_id" : "000000002",
                "speciality" : "Управление в технических системах",
                "profile" : "Аддитивное производство",
                "qualification" : "Бакалавр",
                "graduating_department_name" : ""
            }
        ]
        """
        
        Organization.objects.create(name="ВолгГТУ")

        ReferenceImporter.import_faculty_reference(FACULTY_REFERENCE_DATA)
        ReferenceImporter.import_department_reference(DEPARTMENT_REFERENCE_DATA)
        ReferenceImporter.import_student_reference(STUDENT_REFERENCE_DATA)

        try:
            self.assertEqual(EventParticipant.objects.all().count(), 2)
            self.assertNotEqual(EventParticipant.objects.get(name="АДП-222"), None)
            self.assertEqual(EventParticipant.objects.get(
                role=EventParticipant.Role.STUDENT,
                is_group=True,
                department__name="Кафедра Автоматические установки"
            ).name, "АДП-322")
        except EventParticipant.DoesNotExist:
            self.fail()
