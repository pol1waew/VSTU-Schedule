from api.utilities import ReadAPI, WriteAPI
from api.utility_filters import *
from api.models import Event
from collections import defaultdict


def get_table_data(filters):
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
        reader.add_filter(PlaceFilter.by_repr(filters["place"]))

    if filters["subject"]:
        reader.add_filter(SubjectFilter.by_name(filters["subject"]))
        
    if filters["kind"]:
        reader.add_filter(KindFilter.by_name(filters["kind"]))

    if filters["time_slot"]:
        reader.add_filter(TimeSlotFilter.by_repr(filters["time_slot"]))

    reader.find_models(Event)

    if filters["teacher"]:
        entries = format_events(reader.get_found_models().filter(**ParticipantFilter.by_name(filters["teacher"])).distinct())
    else:
        entries = format_events(reader.get_found_models())

    row_spans = get_row_spans(entries)

    calendar = get_calendar(entries)

    return list(zip(entries, row_spans, calendar))


def format_events(events):
    events = events.order_by("time_slot_override__start_time", "date")

    # grouping by date
    grouped_events = defaultdict(list)

    for e in events:
        grouped_events[e.date].append(e)

    return list(grouped_events.values())


def is_same_entries(first_entry, second_entry):
    return abs(first_entry.time_slot_override.pk - second_entry.time_slot_override.pk) == 1 and \
            first_entry.subject_override == second_entry.subject_override and \
            list(first_entry.get_groups()) == list(second_entry.get_groups()) and \
            list(first_entry.get_teachers()) == list(second_entry.get_teachers()) and \
            list(first_entry.places_override.all()) == list(second_entry.places_override.all())


def get_row_spans(entries):
    row_spans = []

    for entry in entries:
        row_spans.append([])
        prev_event_expanded = False

        for i in range(0, len(entry)):
            # if previous row expanded
            # need to collaspe current
            if prev_event_expanded:
                row_spans[len(row_spans) - 1].append(0)
                prev_event_expanded = False
                continue
            
            """
            # cant wrap rows with canceled events
            if entry[i].is_event_canceled == True:
                row_spans[len(row_spans) - 1].append(1)
                continue
            """
                
            # skip last row
            if i + 1 >= len(entry):
                row_spans[len(row_spans) - 1].append(1)
                continue

            if is_same_entries(entry[i], entry[i + 1]):
                row_spans[len(row_spans) - 1].append(2)
                prev_event_expanded = True
            else:
                row_spans[len(row_spans) - 1].append(1)

    return row_spans


def get_month_name(i):
    '''Returns month name from month number
    '''
    MONTH_NAMES = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    
    return MONTH_NAMES[i - 1]


def get_calendar(entries):
    calendar = []
    dates = [1, 2, 3]

    for entry in entries:
        # list of monthes to show
        monthes = []
        # list of days for every month to show
        days = []
        dates = []
        start_date, end_date, date, repetition_period = WriteAPI.get_semester_filling_parameters(entry[0].abstract_event)

        while date < end_date:
            if date >= start_date:
                dates.append(date)
            
            date += timedelta(days=repetition_period)

        m = start_date.month
        while m <= end_date.month:
            monthes.append(get_month_name(m))

            # list will be empty if month havent any studying day
            days.append([])
            for d in reversed(dates):
                if d.month == m:
                    days[len(days) - 1].append(d.day)
                    dates.remove(d)

            days[len(days) - 1].sort()

            m += 1

        calendar.append([])
        calendar[len(calendar) - 1].append(monthes)
        calendar[len(calendar) - 1].append(format_days(days))
            
        # calendar can be buided from first event in entry
        continue

    return calendar

def format_days(days : list):
    '''
    Transform days order from column (column like month) into row oriented
    '''
    
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
    value = ""

    if name in POST:
        value = POST.getlist(name)

        # converts single value array into value
        if type(value) is list and len(value) == 1:
            value = value[0]

    return value
