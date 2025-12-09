from django.test import TestCase
from api.utilities import Utilities
from api.models import (
    ScheduleTemplateMetadata,
)

"""py manage.py test api.tests.test_utilities
"""

class TestUtilities(TestCase):
    def test_normalize_full_place_repr(self):
        EXPECTED_VALUE = ("В", "902б")

        self.assertSequenceEqual(
            Utilities.normalize_place_repr("В, 902б"),
            EXPECTED_VALUE
        )
        self.assertSequenceEqual(
            Utilities.normalize_place_repr("В,902б"),
            EXPECTED_VALUE
        )
        self.assertSequenceEqual(
            Utilities.normalize_place_repr("В 902б"),
            EXPECTED_VALUE
        )
        self.assertSequenceEqual(
            Utilities.normalize_place_repr("В-902б"),
            EXPECTED_VALUE
        )

    def test_normalize_half_place_repr(self):
        self.assertSequenceEqual(
            Utilities.normalize_place_repr("902б"),
            ("", "902б")
        )
        self.assertEqual(
            Utilities.normalize_place_repr("В-"),
            None
        )
        self.assertSequenceEqual(
            Utilities.normalize_place_repr("В902б"),
            ("", "В902б")
        )

    def test_month_number_into_name(self):
        MONTH_NUMBERS = [1, 6, 12]
        NOT_EXISTING_MONTH_NUMBERS = [0, -12, 13]
        EXISTING_AND_NOT_MONTH_NUMBERS = [9, -1, 3, 99]

        EXPECTED_MONTH_NAMES = ["Январь", "Июнь", "Декабрь"]
        EXPECTED_NOT_EXISTING_MONTH_NAMES = [None, None, None]
        EXPECTED_EXISTING_AND_NOT_MONTH_NAMES = ["Сентябрь", None, "Март", None]

        self.assertEqual(
            Utilities.get_month_name(MONTH_NUMBERS[0]),
            EXPECTED_MONTH_NAMES[0]
        )
        self.assertSequenceEqual(
            Utilities.get_month_name(MONTH_NUMBERS),
            EXPECTED_MONTH_NAMES
        )
        self.assertSequenceEqual(
            Utilities.get_month_name(NOT_EXISTING_MONTH_NUMBERS),
            EXPECTED_NOT_EXISTING_MONTH_NAMES
        )
        self.assertSequenceEqual(
            Utilities.get_month_name(EXISTING_AND_NOT_MONTH_NUMBERS),
            EXPECTED_EXISTING_AND_NOT_MONTH_NAMES
        )

    def test_normalize_time_slot(self):
        self.assertSequenceEqual(
            Utilities.normalize_time_slot_repr("1-2"),
            ("1-2", "", "")
        )
        self.assertSequenceEqual(
            Utilities.normalize_time_slot_repr("13.00"),
            ("", "13:00", "")
        )
        self.assertSequenceEqual(
            Utilities.normalize_time_slot_repr("18:00"),
            ("", "18:00", "")
        )
        self.assertSequenceEqual(
            Utilities.normalize_time_slot_repr("8:30 - 10.00"),
            ("", "8:30", "10:00")
        )
        self.assertSequenceEqual(
            Utilities.normalize_time_slot_repr("8.30 10:00"),
            ("", "8:30", "10:00")
        )

    def test_get_scope_value(self):
        # common
        self.assertEqual(
            Utilities.get_scope_value("бакалавриат"),
            ScheduleTemplateMetadata.Scope.BACHELOR
        )
        self.assertEqual(
            Utilities.get_scope_value("Магистратура"),
            ScheduleTemplateMetadata.Scope.MASTER
        )
        self.assertEqual(
            Utilities.get_scope_value("   аспирантура "),
            ScheduleTemplateMetadata.Scope.POSTGRADUATE
        )
        self.assertEqual(
            Utilities.get_scope_value("Консультация   "),
            ScheduleTemplateMetadata.Scope.CONSULTATION
        )

        self.assertEqual(
            Utilities.get_scope_value("бакалавры"),
            ScheduleTemplateMetadata.Scope.BACHELOR
        )
        self.assertEqual(
            Utilities.get_scope_value(" бакалавров"),
            ScheduleTemplateMetadata.Scope.BACHELOR
        )
        self.assertEqual(
            Utilities.get_scope_value("магистры "),
            ScheduleTemplateMetadata.Scope.MASTER
        )
        self.assertEqual(
            Utilities.get_scope_value("магистров"),
            ScheduleTemplateMetadata.Scope.MASTER
        )
        self.assertEqual(
            Utilities.get_scope_value("  аспиранты "),
            ScheduleTemplateMetadata.Scope.POSTGRADUATE
        )
        self.assertEqual(
            Utilities.get_scope_value(" аспирантов  "),
            ScheduleTemplateMetadata.Scope.POSTGRADUATE
        )
        self.assertEqual(
            Utilities.get_scope_value("консульт."),
            ScheduleTemplateMetadata.Scope.CONSULTATION
        )

        self.assertEqual(
            Utilities.get_scope_value("бак."),
            None
        )
        self.assertEqual(
            Utilities.get_scope_value("асп."),
            None
        )

    def test_replace_roman_with_arabic_numerals(self):
        self.assertEqual(
            Utilities.replace_all_roman_with_arabic_numerals("Учебные занятия 3 курса ФАТ магистров I-ого семестра 2024-2025 учебного года"),
            "Учебные занятия 3 курса ФАТ магистров 1-ого семестра 2024-2025 учебного года"
        )
        self.assertEqual(
            Utilities.replace_all_roman_with_arabic_numerals("Учебные занятия 4 курса ФЭВТ аспирантов на II-й семестр 2023-2024 учебного года"),
            "Учебные занятия 4 курса ФЭВТ аспирантов на 2-й семестр 2023-2024 учебного года"
        )

        self.assertEqual(
            Utilities.replace_all_roman_with_arabic_numerals("X"),
            "10"
        )
        self.assertEqual(
            Utilities.replace_all_roman_with_arabic_numerals("IX"),
            "9"
        )
        self.assertEqual(
            Utilities.replace_all_roman_with_arabic_numerals("VIII II"),
            "8 2"
        )
        self.assertEqual(
            Utilities.replace_all_roman_with_arabic_numerals("VII"),
            "7"
        )
        self.assertEqual(
            Utilities.replace_all_roman_with_arabic_numerals("VI"),
            "6"
        )
        self.assertEqual(
            Utilities.replace_all_roman_with_arabic_numerals("V"),
            "5"
        )
        self.assertEqual(
            Utilities.replace_all_roman_with_arabic_numerals("I IV"),
            "1 4"
        )
        self.assertEqual(
            Utilities.replace_all_roman_with_arabic_numerals("III II I I II III"),
            "3 2 1 1 2 3"
        )
