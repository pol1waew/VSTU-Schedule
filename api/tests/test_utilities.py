from django.test import TestCase
from api.utilities import Utilities

class TestUtilities(TestCase):
    def test_normalize_full_place_repr(self):
        COMMA_AND_SPACE_SEPARATED = "В, 902б"
        COMMA_SEPARATED = "В,902б"
        SPACE_SEPARATED = "В 902б"
        DASH_SEPARATED = "В-902б"

        EXPECTED_VALUE = ("В", "902б")

        self.assertSequenceEqual(
            Utilities.normalize_place_repr(COMMA_AND_SPACE_SEPARATED),
            EXPECTED_VALUE
        )
        self.assertSequenceEqual(
            Utilities.normalize_place_repr(COMMA_SEPARATED),
            EXPECTED_VALUE
        )
        self.assertSequenceEqual(
            Utilities.normalize_place_repr(SPACE_SEPARATED),
            EXPECTED_VALUE
        )
        self.assertSequenceEqual(
            Utilities.normalize_place_repr(DASH_SEPARATED),
            EXPECTED_VALUE
        )

    def test_normalize_half_place_repr(self):
        ONLY_ROOM = "902б"
        ONLY_BUILDING = "В-"
        BUILDING_AND_ROOM_NOT_SEPARATED = "В902б"

        ONLY_ROOM_EXPECTED_VALUE = ("", "902б")
        ONLY_BUILDING_EXPECTED_VALUE = None
        NOT_SEPARATED_EXPECTED_VALUE = ("", "В902б")

        self.assertSequenceEqual(
            Utilities.normalize_place_repr(ONLY_ROOM),
            ONLY_ROOM_EXPECTED_VALUE
        )
        self.assertEqual(
            Utilities.normalize_place_repr(ONLY_BUILDING),
            ONLY_BUILDING_EXPECTED_VALUE
        )
        self.assertSequenceEqual(
            Utilities.normalize_place_repr(BUILDING_AND_ROOM_NOT_SEPARATED),
            NOT_SEPARATED_EXPECTED_VALUE
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