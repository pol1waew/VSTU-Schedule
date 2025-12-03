from api.utilities import Utilities, ReadAPI, WriteAPI
from api.utility_filters import *
from api.models import Event
from collections import defaultdict


def get_table_data(filters):
    """Returns formated data ready to visualisation
    """
    
    reader = ReadAPI()
    
    if filters["date"] == "today":
        reader.add_filter(DateFilter.today())
    elif filters["date"] == "tomorrow":
        reader.add_filter(DateFilter.tomorrow())
    elif filters["date"] == "this_week":
        reader.add_filter(DateFilter.this_week())
    elif filters["date"] == "next_week":
        reader.add_filter(DateFilter.next_week())
    elif filters["date"] == "single_date" and filters["left_date"] != "":
        reader.add_filter(DateFilter.from_singe_date(filters["left_date"]))
    elif filters["date"] == "range_date" and filters["left_date"] != "" and filters["right_date"] != "":
        reader.add_filter(DateFilter.from_date(filters["left_date"], filters["right_date"]))

    if filters["group"]:
        reader.add_filter(ParticipantFilter.by_name(filters["group"]))

    if filters["place"]:
        reader.add_filter(PlaceFilter.by_repr_event_relative(filters["place"]))

    if filters["subject"]:
        reader.add_filter(SubjectFilter.by_name(filters["subject"]))
        
    if filters["kind"]:
        reader.add_filter(KindFilter.by_name(filters["kind"]))

    if filters["time_slot"]:
        reader.add_filter(TimeSlotFilter.by_repr_event_relative(filters["time_slot"]))

    reader.find_models(Event)

    if filters["teacher"]:
        entries = format_events(reader.get_found_models().filter(**ParticipantFilter.by_name(filters["teacher"])).distinct())
    else:
        entries = format_events(reader.get_found_models())

    row_spans = get_row_spans(entries)

    calendar = get_calendar(entries)

    return list(zip(entries, row_spans, calendar))


def format_events(events):
    """Format events by grouping them and ordering by date
    """
    
    events = events.order_by("time_slot_override__start_time", "date")

    # grouping found events by date
    grouped_events = defaultdict(list)

    for e in events:
        grouped_events[e.date].append(e)

    # ordering groups of events by date
    ordered_grouped_events = []

    for e in sorted(grouped_events.items()):
        ordered_grouped_events.append(e[1])

    return ordered_grouped_events


def is_same_entries(first_entry, second_entry):
    """
    Проверяет, считаем ли два события одним и тем же «занятием» для целей UI‑слияния.

    ВАЖНО:
    - Больше НЕ опираемся на разницу pk учебных часов (abs(pk1 - pk2) == 1),
      т.к. это приводит к ложному объединению разных времён (пример 15:20 и 17:00).
    - Считаем события одинаковыми, только если совпадает:
      * время слота (start_time и end_time),
      * предмет и тип занятия,
      * полный набор групп,
      * полный набор преподавателей,
      * набор аудиторий,
      * явная дата проведения (holds_on_date) у абстрактных событий.
    """

    ts1 = first_entry.time_slot_override
    ts2 = second_entry.time_slot_override

    if not ts1 or not ts2:
        return False

    same_time = (
        ts1.start_time == ts2.start_time and
        ts1.end_time == ts2.end_time
    )
    if not same_time:
        return False

    if first_entry.subject_override_id != second_entry.subject_override_id:
        return False

    if first_entry.kind_override_id != second_entry.kind_override_id:
        return False

    first_groups = tuple(sorted(first_entry.get_groups().values_list("pk", flat=True)))
    second_groups = tuple(sorted(second_entry.get_groups().values_list("pk", flat=True)))
    if first_groups != second_groups:
        return False

    first_teachers = tuple(sorted(first_entry.get_teachers().values_list("pk", flat=True)))
    second_teachers = tuple(sorted(second_entry.get_teachers().values_list("pk", flat=True)))
    if first_teachers != second_teachers:
        return False

    first_places = tuple(sorted(first_entry.places_override.values_list("pk", flat=True)))
    second_places = tuple(sorted(second_entry.places_override.values_list("pk", flat=True)))
    if first_places != second_places:
        return False

    if first_entry.abstract_event.holds_on_date != second_entry.abstract_event.holds_on_date:
        return False

    return True


def get_row_spans(entries):
    """
    Строит матрицу rowSpan'ов для таблицы.

    Для каждого дня (список Events) ищем серии подряд идущих одинаковых событий:
    - для первого элемента серии ставим rowSpan = длина серии,
    - для остальных элементов серии ставим 0 (ячейка в шаблоне не рисуется).

    Примеры:
    - [A, A, A] → [3, 0, 0]
    - [A, B, B, C] → [1, 2, 0, 1]
    - [A(11:50), A(13:40)] с разным временем → [1, 1] (не сливаются).
    """

    row_spans: list[list[int]] = []

    for day_events in entries:
        spans_for_day: list[int] = []
        i = 0

        while i < len(day_events):
            run_length = 1
            while (
                i + run_length < len(day_events)
                and is_same_entries(day_events[i], day_events[i + run_length])
            ):
                run_length += 1

            spans_for_day.append(run_length)
            for _ in range(1, run_length):
                spans_for_day.append(0)

            i += run_length

        row_spans.append(spans_for_day)

    return row_spans

def get_calendar(entries):
    """Makes and returns calendar for given entries

    Calendar format:
    [
        [['Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь', 'Январь'], [[1, 13, 10, 8, 5], [15, 27, 24, 22, 19], [29, '', '', '', '']]]
    ]
    """
    
    calendar = []

    for entry in entries:
        months = []
        month_days = []
        dates = []
        _, end_date, date, repetition_period = WriteAPI.get_semester_filling_parameters(entry[0].abstract_event)


        while date < end_date:
            if not date.month in months:
                months.append(date.month)

                if dates:
                    month_days.append(dates)
                    dates = []
                
            dates.append(date.day)
            
            date += timedelta(days=repetition_period)
        
        if dates:
            month_days.append(dates)
            dates = []

        calendar.append([])
        calendar[len(calendar) - 1].append(Utilities.get_month_name(months))
        calendar[len(calendar) - 1].append(format_days(month_days))

        # calendar can be builded from first event each day
        continue

    return calendar


def format_days(days : list):
    """Transforms days order from column into row oriented
    """
    
    max_days_count = 0
    formated_days = []

    for d in days:
        if (len(d) > max_days_count):
            max_days_count = len(d)

    for i in range(max_days_count):
        row = []
        for d in days:
            if (i >= len(d)):
                row.append("")
                continue
            row.append(d[i])

        formated_days.append(row)

    return formated_days


def get_POST_value(POST, name):
    """Returns POST value by represented name
    """
    
    value = ""

    if name in POST:
        value = POST.getlist(name)

        # converts single value array into value
        if type(value) is list and len(value) == 1:
            value = value[0]

    return value
