from django.test import TestCase
from api.utilities import Utilities

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
        self.assertEqual(
            Utilities.normalize_time_slot_repr("1-2"),
            "1-2"
        )
        self.assertEqual(
            Utilities.normalize_time_slot_repr("13.00"),
            "13:00"
        )
        self.assertEqual(
            Utilities.normalize_time_slot_repr("18:00"),
            "18:00"
        )
        self.assertEqual(
            Utilities.normalize_time_slot_repr("8:30-10.00"),
            "8:30 10:00"
        )
        self.assertEqual(
            Utilities.normalize_time_slot_repr("8.30 10:00"),
            "8:30 10:00"
        )
