from datetime import datetime
from django.test import TestCase
from api.importers import EventImporter, ReferenceImporter
from api.utilities import WriteAPI, EventImportAPI
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
    SCHEDULE_REFERENCE_DATA = """
        [
            {
                "course": "4",
                "schedule_template_metadata_faculty_shortname": "ФЭВТ",
                "semester": "2",
                "years": "2024-2025",
                "start_date": "01.09.2024",
                "end_date": "01.02.2025",
                "scope": "Бакалавриат",
                "department_shortname": "ФЭВТ"
            }
        ]
    """
    
    def setUp(self):
        WriteAPI.create_common_abstract_days()
        Organization.objects.create(name="ВолгГТУ")
        ReferenceImporter.import_faculty_reference(self.FACULTY_REFERENCE_DATA)
        ReferenceImporter.import_schedule(self.SCHEDULE_REFERENCE_DATA, True)
        #self.create_abstract_days() ## TODO: replace with WriteAPI.create_common_abstract_days
        #self.create_time_slots()
        #self.create_schedule() ## TODO: replace with Schedule importer

    def create_time_slots(self):
        TimeSlot.objects.bulk_create([
                TimeSlot(alt_name="1-2", start_time=datetime.strptime("08:30:00", "%H:%M:%S"), end_time=datetime.strptime("10:00:00", "%H:%M:%S")),
                TimeSlot(alt_name="3-4", start_time=datetime.strptime("10:10:00", "%H:%M:%S"), end_time=datetime.strptime("11:40:00", "%H:%M:%S")),
                TimeSlot(alt_name="5-6", start_time=datetime.strptime("11:50:00", "%H:%M:%S"), end_time=datetime.strptime("13:20:00", "%H:%M:%S")),
                TimeSlot(alt_name="7-8", start_time=datetime.strptime("13:40:00", "%H:%M:%S"), end_time=datetime.strptime("15:10:00", "%H:%M:%S")),
                TimeSlot(alt_name="9-10", start_time=datetime.strptime("15:20:00", "%H:%M:%S"), end_time=datetime.strptime("16:50:00", "%H:%M:%S")),
                TimeSlot(alt_name="11-12", start_time=datetime.strptime("17:00:00", "%H:%M:%S"), end_time=datetime.strptime("18:30:00", "%H:%M:%S"))
        ])
 
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
            self.assertEqual(TimeSlot.objects.all().count(), 4)
            self.assertNotEqual(TimeSlot.objects.get(start_time__contains="8:30"), None)
            self.assertNotEqual(TimeSlot.objects.get(start_time__contains="11:55"), None)
            self.assertNotEqual(TimeSlot.objects.get(end_time__contains="15:01"), None)
            self.assertNotEqual(TimeSlot.objects.get(end_time__contains="15:10"), None)
        except TimeSlot.DoesNotExist:
            self.fail()

    def test_import_events_for_only_active_schedule(self):
        ReferenceImporter.import_schedule(self.SCHEDULE_REFERENCE_DATA, True)

        try:
            self.assertEqual(Schedule.objects.all().count(), 2)
            self.assertEqual(Schedule.objects.filter(status=Schedule.Status.ACTIVE).count(), 1)
            self.assertEqual(Schedule.objects.filter(status=Schedule.Status.ARCHIVE).count(), 1)
        except Schedule.DoesNotExist:
            self.fail()
        
        try:
            self.assertEqual(
                AbstractEvent.objects.filter(schedule__status=Schedule.Status.ACTIVE).count(),
                AbstractEvent.objects.all().count()
            )
            self.assertEqual(
                AbstractEvent.objects.filter(schedule__status=Schedule.Status.ARCHIVE).count(),
                0
            )
        except AbstractEvent.DoesNotExist:
            self.fail()

    def test_find_schedule(self):
        self.assertEqual(
            EventImportAPI.find_schedule("Учебные занятия 4 курса ФЭВТ бакалавриат на 2 семестр 2024-2025 учебного года"),
            Schedule.objects.get(schedule_template__metadata__faculty="ФЭВТ")
        )
        self.assertRaises(
            ValueError,
            EventImportAPI.find_schedule,
            ""
        )
        self.assertRaises(
            Schedule.DoesNotExist,
            EventImportAPI.find_schedule,
            "Учебные занятия 22 курса АБВГ на 0 семестр 1999-9999 учебного года"
        )
            


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

    def test_schedule_import_saving_archive(self):
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
        SCHEDULE_REFERENCE_DATA = """
            [
                {
                    "course": "4",
                    "schedule_template_metadata_faculty_shortname": "ФЭВТ",
                    "semester": "1",
                    "years": "2024-2025",
                    "start_date": "01.09.2025",
                    "end_date": "01.02.2026",
                    "scope": "бакалавриат",
                    "department_shortname": "ФЭВТ"
                },
                {
                    "course": "4",
                    "schedule_template_metadata_faculty_shortname": "ХТФ",
                    "semester": "1",
                    "years": "2024-2025",
                    "start_date": "01.09.2025",
                    "end_date": "01.02.2026",
                    "scope": "  магистратура ",
                    "department_shortname": "ХТФ"
                },
                {
                    "course": "3",
                    "schedule_template_metadata_faculty_shortname": "ФЭВТ",
                    "semester": "1",
                    "years": "2024-2025",
                    "start_date": "01.09.2025",
                    "end_date": "01.02.2026",
                    "scope": " Магистратура",
                    "department_shortname": "ФЭВТ"
                }
            ]
        """

        Organization.objects.create(name="ВолгГТУ")
        if not WriteAPI.create_common_abstract_days():
            self.fail()

        ReferenceImporter.import_faculty_reference(FACULTY_REFERENCE_DATA)

        # first import
        ReferenceImporter.import_schedule(SCHEDULE_REFERENCE_DATA, True)

        try:
            self.assertEqual(Schedule.objects.all().count(), 3)
            self.assertEqual(Schedule.objects.filter(status=Schedule.Status.ACTIVE).count(), 3)
            self.assertEqual(Schedule.objects.filter(status=Schedule.Status.ARCHIVE).count(), 0)
            self.assertNotEqual(
                Schedule.objects.get(
                    status=Schedule.Status.ACTIVE,
                    schedule_template__metadata__faculty="ФЭВТ",
                    metadata__course=4
                ),
                None
            )
            self.assertNotEqual(
                Schedule.objects.get(
                    status=Schedule.Status.ACTIVE,
                    schedule_template__metadata__faculty="ФЭВТ",
                    metadata__course=3
                ),
                None
            )
        except Schedule.DoesNotExist:
            self.fail()

        # 4 course 1 semester 2024-2025
        # 3 course 1 semester 2024-2025
        try:
            self.assertEqual(ScheduleMetadata.objects.all().count(), 2)
        except ScheduleMetadata.DoesNotExist:
            self.fail()

        # Факультет электроники и вычислительной техники (Бакалавриат)
        # Факультет электроники и вычислительной техники (Магистратура)
        # Химико-технологический факультет
        try:
            self.assertEqual(ScheduleTemplate.objects.all().count(), 3)
        except ScheduleTemplate.DoesNotExist:
            self.fail()
        
        # ФЭВТ, Бакалавриат
        # ФЭВТ, Магистратура
        # ХТФ, Магистратура
        try:
            self.assertEqual(ScheduleTemplateMetadata.objects.all().count(), 3)
        except ScheduleTemplateMetadata.DoesNotExist:
            self.fail()

        # second import
        # now we have ARCHIVE Schedules
        ReferenceImporter.import_schedule(SCHEDULE_REFERENCE_DATA, True)

        try:
            self.assertEqual(Schedule.objects.all().count(), 6)
            self.assertEqual(Schedule.objects.filter(status=Schedule.Status.ACTIVE).count(), 3)
            self.assertEqual(Schedule.objects.filter(status=Schedule.Status.ARCHIVE).count(), 3)
            self.assertEqual(
                Schedule.objects.filter(
                    status=Schedule.Status.ACTIVE,
                    schedule_template__metadata__faculty="ФЭВТ",
                    metadata__course=4
                ).count(),
                1
            )
            self.assertEqual(
                Schedule.objects.filter(
                    status=Schedule.Status.ACTIVE,
                    schedule_template__metadata__faculty="ХТФ",
                    metadata__course=4
                ).count(),
                1
            )
            self.assertEqual(
                Schedule.objects.filter(
                    status=Schedule.Status.ARCHIVE,
                    schedule_template__metadata__faculty="ХТФ",
                    metadata__course=4
                ).count(),
                1
            )
        except Schedule.DoesNotExist:
            self.fail()

        # nothing must change
        # 4 course 1 semester 2024-2025
        # 3 course 1 semester 2024-2025
        try:
            self.assertEqual(ScheduleMetadata.objects.all().count(), 2)
        except ScheduleMetadata.DoesNotExist:
            self.fail()

        # Факультет электроники и вычислительной техники (Бакалавриат)
        # Факультет электроники и вычислительной техники (Магистратура)
        # Химико-технологический факультет
        try:
            self.assertEqual(ScheduleTemplate.objects.all().count(), 3)
        except ScheduleTemplate.DoesNotExist:
            self.fail()
        
        # ФЭВТ, Бакалавриат
        # ФЭВТ, Магистратура
        # ХТФ, Магистратура
        try:
            self.assertEqual(ScheduleTemplateMetadata.objects.all().count(), 3)
        except ScheduleTemplateMetadata.DoesNotExist:
            self.fail()

        # third import
        ReferenceImporter.import_schedule(SCHEDULE_REFERENCE_DATA, True)

        try:
            self.assertEqual(Schedule.objects.all().count(), 9)
            self.assertEqual(Schedule.objects.filter(status=Schedule.Status.ACTIVE).count(), 3)
            self.assertEqual(Schedule.objects.filter(status=Schedule.Status.ARCHIVE).count(), 6)
            self.assertEqual(
                Schedule.objects.filter(
                    status=Schedule.Status.ACTIVE,
                    schedule_template__metadata__faculty="ФЭВТ",
                    metadata__course=4
                ).count(),
                1
            )
            self.assertEqual(
                Schedule.objects.filter(
                    status=Schedule.Status.ACTIVE,
                    schedule_template__metadata__faculty="ХТФ",
                    metadata__course=4
                ).count(),
                1
            )
            self.assertEqual(
                Schedule.objects.filter(
                    status=Schedule.Status.ARCHIVE,
                    schedule_template__metadata__faculty="ХТФ",
                    metadata__course=4
                ).count(),
                2
            )
        except Schedule.DoesNotExist:
            self.fail()

        # nothing must change
        # 4 course 1 semester 2024-2025
        # 3 course 1 semester 2024-2025
        try:
            self.assertEqual(ScheduleMetadata.objects.all().count(), 2)
        except ScheduleMetadata.DoesNotExist:
            self.fail()

        # Факультет электроники и вычислительной техники (Бакалавриат)
        # Факультет электроники и вычислительной техники (Магистратура)
        # Химико-технологический факультет
        try:
            self.assertEqual(ScheduleTemplate.objects.all().count(), 3)
        except ScheduleTemplate.DoesNotExist:
            self.fail()
        
        # ФЭВТ, Бакалавриат
        # ФЭВТ, Магистратура
        # ХТФ, Магистратура
        try:
            self.assertEqual(ScheduleTemplateMetadata.objects.all().count(), 3)
        except ScheduleTemplateMetadata.DoesNotExist:
            self.fail()

    def test_schedule_import_deleting_archive(self):
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
        SCHEDULE_REFERENCE_DATA = """
            [
                {
                    "course": "4",
                    "schedule_template_metadata_faculty_shortname": "ФЭВТ",
                    "semester": "1",
                    "years": "2024-2025",
                    "start_date": "01.09.2025",
                    "end_date": "01.02.2026",
                    "scope": "бакалавриат",
                    "department_shortname": "ФЭВТ"
                },
                {
                    "course": "4",
                    "schedule_template_metadata_faculty_shortname": "ХТФ",
                    "semester": "1",
                    "years": "2024-2025",
                    "start_date": "01.09.2025",
                    "end_date": "01.02.2026",
                    "scope": "  магистратура ",
                    "department_shortname": "ХТФ"
                },
                {
                    "course": "3",
                    "schedule_template_metadata_faculty_shortname": "ФЭВТ",
                    "semester": "1",
                    "years": "2024-2025",
                    "start_date": "01.09.2025",
                    "end_date": "01.02.2026",
                    "scope": " Магистратура",
                    "department_shortname": "ФЭВТ"
                }
            ]
        """

        Organization.objects.create(name="ВолгГТУ")
        if not WriteAPI.create_common_abstract_days():
            self.fail()

        ReferenceImporter.import_faculty_reference(FACULTY_REFERENCE_DATA)

        # first import
        ReferenceImporter.import_schedule(SCHEDULE_REFERENCE_DATA, False)

        try:
            self.assertEqual(Schedule.objects.all().count(), 3)
            self.assertEqual(Schedule.objects.filter(status=Schedule.Status.ACTIVE).count(), 3)
            self.assertEqual(Schedule.objects.filter(status=Schedule.Status.ARCHIVE).count(), 0)
            self.assertNotEqual(
                Schedule.objects.get(
                    status=Schedule.Status.ACTIVE,
                    schedule_template__metadata__faculty="ФЭВТ",
                    metadata__course=4
                ),
                None
            )
            self.assertNotEqual(
                Schedule.objects.get(
                    status=Schedule.Status.ACTIVE,
                    schedule_template__metadata__faculty="ФЭВТ",
                    metadata__course=3
                ),
                None
            )
        except Schedule.DoesNotExist:
            self.fail()

        # 4 course 1 semester 2024-2025
        # 3 course 1 semester 2024-2025
        try:
            self.assertEqual(ScheduleMetadata.objects.all().count(), 2)
        except ScheduleMetadata.DoesNotExist:
            self.fail()

        # Факультет электроники и вычислительной техники (Бакалавриат)
        # Факультет электроники и вычислительной техники (Магистратура)
        # Химико-технологический факультет
        try:
            self.assertEqual(ScheduleTemplate.objects.all().count(), 3)
        except ScheduleTemplate.DoesNotExist:
            self.fail()
        
        # ФЭВТ, Бакалавриат
        # ФЭВТ, Магистратура
        # ХТФ, Магистратура
        try:
            self.assertEqual(ScheduleTemplateMetadata.objects.all().count(), 3)
        except ScheduleTemplateMetadata.DoesNotExist:
            self.fail()

        # second import
        # now we have ARCHIVE Schedules
        ReferenceImporter.import_schedule(SCHEDULE_REFERENCE_DATA, False)

        try:
            self.assertEqual(Schedule.objects.all().count(), 6)
            self.assertEqual(Schedule.objects.filter(status=Schedule.Status.ACTIVE).count(), 3)
            self.assertEqual(Schedule.objects.filter(status=Schedule.Status.ARCHIVE).count(), 3)
            self.assertEqual(
                Schedule.objects.filter(
                    status=Schedule.Status.ACTIVE,
                    schedule_template__metadata__faculty="ФЭВТ",
                    metadata__course=4
                ).count(),
                1
            )
            self.assertEqual(
                Schedule.objects.filter(
                    status=Schedule.Status.ACTIVE,
                    schedule_template__metadata__faculty="ХТФ",
                    metadata__course=4
                ).count(),
                1
            )
            self.assertEqual(
                Schedule.objects.filter(
                    status=Schedule.Status.ARCHIVE,
                    schedule_template__metadata__faculty="ХТФ",
                    metadata__course=4
                ).count(),
                1
            )
        except Schedule.DoesNotExist:
            self.fail()

        # nothing must change
        # 4 course 1 semester 2024-2025
        # 3 course 1 semester 2024-2025
        try:
            self.assertEqual(ScheduleMetadata.objects.all().count(), 2)
        except ScheduleMetadata.DoesNotExist:
            self.fail()

        # Факультет электроники и вычислительной техники (Бакалавриат)
        # Факультет электроники и вычислительной техники (Магистратура)
        # Химико-технологический факультет
        try:
            self.assertEqual(ScheduleTemplate.objects.all().count(), 3)
        except ScheduleTemplate.DoesNotExist:
            self.fail()
        
        # ФЭВТ, Бакалавриат
        # ФЭВТ, Магистратура
        # ХТФ, Магистратура
        try:
            self.assertEqual(ScheduleTemplateMetadata.objects.all().count(), 3)
        except ScheduleTemplateMetadata.DoesNotExist:
            self.fail()

        # third import
        ReferenceImporter.import_schedule(SCHEDULE_REFERENCE_DATA, False)

        try:
            self.assertEqual(Schedule.objects.all().count(), 6)
            self.assertEqual(Schedule.objects.filter(status=Schedule.Status.ACTIVE).count(), 3)
            self.assertEqual(Schedule.objects.filter(status=Schedule.Status.ARCHIVE).count(), 3)
            self.assertEqual(
                Schedule.objects.filter(
                    status=Schedule.Status.ACTIVE,
                    schedule_template__metadata__faculty="ФЭВТ",
                    metadata__course=4
                ).count(),
                1
            )
            self.assertEqual(
                Schedule.objects.filter(
                    status=Schedule.Status.ACTIVE,
                    schedule_template__metadata__faculty="ХТФ",
                    metadata__course=4
                ).count(),
                1
            )
            self.assertEqual(
                Schedule.objects.filter(
                    status=Schedule.Status.ARCHIVE,
                    schedule_template__metadata__faculty="ХТФ",
                    metadata__course=4
                ).count(),
                1
            )
        except Schedule.DoesNotExist:
            self.fail()

        # nothing must change
        # 4 course 1 semester 2024-2025
        # 3 course 1 semester 2024-2025
        try:
            self.assertEqual(ScheduleMetadata.objects.all().count(), 2)
        except ScheduleMetadata.DoesNotExist:
            self.fail()

        # Факультет электроники и вычислительной техники (Бакалавриат)
        # Факультет электроники и вычислительной техники (Магистратура)
        # Химико-технологический факультет
        try:
            self.assertEqual(ScheduleTemplate.objects.all().count(), 3)
        except ScheduleTemplate.DoesNotExist:
            self.fail()
        
        # ФЭВТ, Бакалавриат
        # ФЭВТ, Магистратура
        # ХТФ, Магистратура
        try:
            self.assertEqual(ScheduleTemplateMetadata.objects.all().count(), 3)
        except ScheduleTemplateMetadata.DoesNotExist:
            self.fail()

    # TODO: schedule_import test with event deleting
