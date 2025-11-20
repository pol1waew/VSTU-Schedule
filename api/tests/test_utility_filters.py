from datetime import datetime
from django.test import TestCase
from api.models import TimeSlot, EventPlace
from api.utility_filters import TimeSlotFilter, PlaceFilter

"""py manage.py test api.tests.test_utility_filters
"""

class TestTimeSlotFiltering(TestCase):
    def setUp(self):
        self.first_time_slot = TimeSlot.objects.create(
            alt_name="1-2", 
            start_time=datetime.strptime("8:30", "%H:%M"), 
            end_time=datetime.strptime("10:00", "%H:%M")
        )
        self.second_time_slot = TimeSlot.objects.create(
            alt_name=None, 
            start_time=datetime.strptime("10:10", "%H:%M"), 
            end_time=datetime.strptime("11:40", "%H:%M")
        )
        self.third_time_slot = TimeSlot.objects.create(
            alt_name=None, 
            start_time=datetime.strptime("11:50", "%H:%M"), 
            end_time=None
        )

    def test_repr_filter(self):
        SINGLE_ALT_NAME_REPR = "1-2"
        MULTIPLE_ALT_NAMES_REPR = ["1-2", "3-4"]
        WITH_WRONG_ALT_NAME_REPR = ["1-2", "3.4", "11-12"]
        SINGLE_START_TIME_REPR = "22:05"
        MULTIPLE_START_TIMES_REPR = ["11:11", "12:12"]
        WITH_WRONG_START_TIMES_REPR = ["9:09", "3:03", "21:00", "21.22"]
        COMBINED_ALT_NAME_AND_START_TIME_REPR = ["3-4", "5.6", "9-10", "9:10"]

        EXPECTED_SINGLE_ALT_NAME_RESULT = {"alt_name" : "1-2"}
        EXPECTED_MULTIPLE_ALT_NAMES_RESULT = {"alt_name__in" : ["1-2", "3-4"]}
        EXPECTED_WITH_WRONG_ALT_NAME_RESULT = {"alt_name__in" : ["1-2", "11-12"]}
        EXPECTED_SINGLE_START_TIME_RESULT = {"start_time__contains" : "22:05"}
        EXPECTED_MULTIPLE_START_TIMES_RESULT = {"start_time__in" : ["11:11", "12:12"]}
        EXPECTED_WITH_WRONG_START_TIMES_RESULT = {"start_time__in" : ["9:09", "3:03", "21:00"]}
        EXPECTED_COMBINED_ALT_NAME_AND_START_TIME_RESULT = {"start_time__contains" : "9:10"}

        self.assertSequenceEqual(
            TimeSlotFilter.by_repr(SINGLE_ALT_NAME_REPR),
            EXPECTED_SINGLE_ALT_NAME_RESULT
        )
        self.assertSequenceEqual(
            TimeSlotFilter.by_repr(MULTIPLE_ALT_NAMES_REPR),
            EXPECTED_MULTIPLE_ALT_NAMES_RESULT
        )
        self.assertSequenceEqual(
            TimeSlotFilter.by_repr(WITH_WRONG_ALT_NAME_REPR),
            EXPECTED_WITH_WRONG_ALT_NAME_RESULT
        )
        self.assertSequenceEqual(
            TimeSlotFilter.by_repr(SINGLE_START_TIME_REPR),
            EXPECTED_SINGLE_START_TIME_RESULT
        )
        self.assertSequenceEqual(
            TimeSlotFilter.by_repr(MULTIPLE_START_TIMES_REPR),
            EXPECTED_MULTIPLE_START_TIMES_RESULT
        )
        self.assertSequenceEqual(
            TimeSlotFilter.by_repr(WITH_WRONG_START_TIMES_REPR),
            EXPECTED_WITH_WRONG_START_TIMES_RESULT
        )
        self.assertSequenceEqual(
            TimeSlotFilter.by_repr(COMBINED_ALT_NAME_AND_START_TIME_REPR),
            EXPECTED_COMBINED_ALT_NAME_AND_START_TIME_RESULT
        )

    def test_repr_filter_and_find(self):
        self.assertEqual(
            TimeSlot.objects.get(**TimeSlotFilter.by_repr("1-2")),
            self.first_time_slot
        )
        self.assertEqual(
            TimeSlot.objects.get(**TimeSlotFilter.by_repr("10:10")),
            self.second_time_slot
        )
        self.assertEqual(
            TimeSlot.objects.get(**TimeSlotFilter.by_repr("11:50")),
            self.third_time_slot
        )

    def test_alt_name_filter(self):
        # TimeSlot alt_names such as '0-0' '9-8' '10-15' '10-00'
        # will be correct
        MULTIPLE_ALT_NAMES = ["1-2", "0-0", "9-8"]
        MULTIPLE_ALT_NAMES_COMBINED = ["10-15", "11.11", "12:32", "10-00"]

        EXPECTED_SINGLE_CORRECT_RESULT = ({"alt_name" : "11-12"}, [])
        EXPECTED_SINGLE_WRONG_RESULT = ({}, ["18:05"])
        EXPECTED_MULTIPLE_CORRENT_RESULTS = ({"alt_name__in" : ["1-2", "0-0", "9-8"]}, [])
        EXPECTED_MULTIPLE_COMBINED_RESULTS = ({"alt_name__in" : ["10-15", "10-00"]}, ["11.11", "12:32"])

        self.assertSequenceEqual(
            TimeSlotFilter.by_alt_name("11-12"),
            EXPECTED_SINGLE_CORRECT_RESULT
        )
        self.assertSequenceEqual(
            TimeSlotFilter.by_alt_name("18:05"),
            EXPECTED_SINGLE_WRONG_RESULT
        )
        self.assertSequenceEqual(
            TimeSlotFilter.by_alt_name(MULTIPLE_ALT_NAMES),
            EXPECTED_MULTIPLE_CORRENT_RESULTS
        )
        self.assertSequenceEqual(
            TimeSlotFilter.by_alt_name(MULTIPLE_ALT_NAMES_COMBINED),
            EXPECTED_MULTIPLE_COMBINED_RESULTS
        )

    def test_start_time_filter(self):
        MULTIPLE_START_TIMES = ["18:05", "8:30 10:00", "15:30"]
        MULTIPLE_START_TIMES_WITH_SOME_WRONG = ["11:11", "23-12", "2:09", "14.25"]

        EXPECTED_COLON_RESULT = ({"start_time__contains" : "18:05"}, [])
        EXPECTED_MULTIPLE_START_TIMES_RESULTS = ({"start_time__in" : ["18:05", "8:30", "15:30"]}, [])
        EXPECTED_WITH_SOME_WRONG_RESULT = ({"start_time__in" : ["11:11", "2:09"]}, ["23-12", "14.25"])

        self.assertSequenceEqual(
            TimeSlotFilter.by_start_time("18:05"),
            EXPECTED_COLON_RESULT
        )
        self.assertSequenceEqual(
            TimeSlotFilter.by_start_time(MULTIPLE_START_TIMES),
            EXPECTED_MULTIPLE_START_TIMES_RESULTS
        )
        self.assertSequenceEqual(
            TimeSlotFilter.by_start_time(MULTIPLE_START_TIMES_WITH_SOME_WRONG),
            EXPECTED_WITH_SOME_WRONG_RESULT
        )        

class TestPlaceFiltering(TestCase):
    def setUp(self):
        self.first_place = EventPlace.objects.create(
            building="В",
            room="902а"
        )
        self.second_place = EventPlace.objects.create(
            building="А",
            room="101"
        )
        self.third_place = EventPlace.objects.create(
            building="",
            room="101"
        )
        self.fourth_place = EventPlace.objects.create(
            building="",
            room="А101"
        )

    def test_repr_filter(self):
        self.assertEqual(
            PlaceFilter.by_repr("ГУК 100"),
            {"building" : "ГУК", "room" : "100"}
        )
        self.assertEqual(
            PlaceFilter.by_repr("ГУК,100"),
            {"building" : "ГУК", "room" : "100"}
        )
        self.assertEqual(
            PlaceFilter.by_repr("ГУК, 100"),
            {"building" : "ГУК", "room" : "100"}
        )
        self.assertEqual(
            PlaceFilter.by_repr("ГУК-100"),
            {"building" : "ГУК", "room" : "100"}
        )
        self.assertEqual(
            PlaceFilter.by_repr("312"),
            {"building" : "", "room" : "312"}
        )
        self.assertEqual(
            PlaceFilter.by_repr(["А 211е", "Б 320з"]),
            {"building__in" : ["А", "Б"], "room__in" : ["211е", "320з"]}
        )
        self.assertEqual(
            PlaceFilter.by_repr(["101", "102"]),
            {"building__in" : ["", ""], "room__in" : ["101", "102"]}
        )
        self.assertEqual(
            PlaceFilter.by_repr(["А211е", "Б320з"]),
            {"building__in" : ["", ""], "room__in" : ["А211е", "Б320з"]}
        )

    def test_repr_filter_and_find(self):
        self.assertEqual(
            EventPlace.objects.get(**PlaceFilter.by_repr("В-902а")),
            self.first_place
        )
        self.assertSequenceEqual(
            list(EventPlace.objects.filter(**PlaceFilter.by_repr(["В-902а", "А101"])).all()),
            [self.first_place, self.fourth_place]
        )
        self.assertEqual(
            EventPlace.objects.get(**PlaceFilter.by_repr("101")),
            self.third_place
        )
        self.assertEqual(
            EventPlace.objects.get(**PlaceFilter.by_repr("А101")),
            self.fourth_place
        )
        # carefully with order
        self.assertEqual(
            list(EventPlace.objects.filter(**PlaceFilter.by_repr(["А101", "А 101", "101"])).all().order_by("building", "room")),
            [self.third_place, self.fourth_place, self.second_place]
        )

    def test_building_filter(self):
        self.assertEqual(
            PlaceFilter.by_building("ГУК"),
            {"building" : "ГУК"}
        )
        self.assertEqual(
            PlaceFilter.by_building(["А", "Б"]),
            {"building__in" : ["А", "Б"]}
        )

    def test_room_filter(self):
        self.assertEqual(
            PlaceFilter.by_room("902а"),
            {"room" : "902а"}
        )
        self.assertEqual(
            PlaceFilter.by_room(["100", "602а"]),
            {"room__in" : ["100", "602а"]}
        )
