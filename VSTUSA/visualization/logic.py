from api.utilities import ReadAPI
from api.utilityFilters import *
from api.models import (
    Event, 
    EventParticipant, 
    EventPlace
)
from datetime import datetime
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
        return format_events(reader.get_found_models().filter(**ParticipantFilter.by_name(filters["teacher"])).distinct())
    else:
        return format_events(reader.get_found_models())

def format_events(events):
    events = events.order_by("time_slot_override__start_time", "date")

    # grouping by date
    grouped_events = defaultdict(list)

    for e in events:
        grouped_events[e.date].append(e)

    entries = list(grouped_events.values())

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
            
            # cant wrap rows with canceled events
            if entry[i].is_event_canceled == True:
                row_spans[len(row_spans) - 1].append(1)
                continue

            # skip last row
            if i + 1 >= len(entry):
                row_spans[len(row_spans) - 1].append(1)
                continue

            if entry[i].subject_override == entry[i + 1].subject_override and \
                abs(entry[i].time_slot_override.pk - entry[i + 1].time_slot_override.pk) == 1:
                row_spans[len(row_spans) - 1].append(2)
                prev_event_expanded = True
            else:
                row_spans[len(row_spans) - 1].append(1)
            
    return list(zip(entries, row_spans))







def getDates(option : int):
    dates = []

    if (option == 0):
        dates = ["2024-10-21"]
    elif (option == 1):
        dates = ["2024-10-22"]
    elif (option == 2):
        dates = ["2024-10-21", "2024-10-22", "2024-10-23", "2024-10-24", "2024-10-25", "2024-10-26", "2024-10-27"]
    elif (option == 3):
        dates = ["2024-10-28", "2024-10-29", "2024-10-30", "2024-10-31", "2024-11-1", "2024-11-2", "2024-11-3"]

    return dates

    # remove dates with no lessons
    for d in reversed(dates):
        if (EventHolding.objects.filter(date = d).first() == None):
            dates.remove(d)

    return dates

def dateToWeekDay(date):
    num = datetime.strptime(date, '%Y-%m-%d').date().weekday()
    names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресение"]

    return names[num]
    
def numberToMonthName(num):
    names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    
    return names[num - 1]

def dayToWeekNumber(date):
    return "1" if datetime.strptime(date, '%Y-%m-%d').date().isocalendar()[1] % 2 == 1 else "2" 

    

def formatArray(array):
    size = 0

    for e in array:
        if (len(e) > size):
            size = len(e)

    formatedArray = []

    for i in range(size):
        entry = []
        for e in array:
            if (i >= len(e)):
                entry.append("")
                continue
            entry.append(e[i])

        formatedArray.append(entry)

    return formatedArray

def getCalendar(forDate : str):
    return
    holding = EventHolding.objects.filter(date = forDate)[0]
    holdings = EventHolding.objects.filter(event_id = holding.event_id)

    months = []
    daysEntry = []
    monthDays = []

    for h in holdings:
        if (numberToMonthName(h.date.month) not in months):
            months.append(numberToMonthName(h.date.month))
            if (not monthDays == []):
                daysEntry.append(monthDays)
                monthDays = []
        if (h.date.day not in monthDays):
            monthDays.append(h.date.day)
    daysEntry.append(monthDays)

    return [months, formatArray(daysEntry)]

def getSelectOptions(sortFilter : int):
    options = []

    if (sortFilter == 0):
        participants = EventParticipant.objects.filter(role = "student")
        for p in participants:
            options.append(p.name)
    elif (sortFilter == 1):
        participants = EventParticipant.objects.filter(role = "teacher")
        for p in participants:
            options.append(p.name)
    else:
        places = EventPlace.objects.all()
        for p in places:
            options.append(p.building + " " + p.room)

    return options