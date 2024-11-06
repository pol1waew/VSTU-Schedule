from django.shortcuts import render
from django.template.defaulttags import register
from visualization.logic import *

@register.filter
def getItem(_dict, key):
    _dict
    return _dict.get(key)


def index(request):
    dates = []
    entries = {}
    weekDays = {}
    weekNumber = {}

    filters = {"date" :  int(request.GET.get("date", 2)),
               "sort" :  int(request.GET.get("sort", 0)),
               "option" :  request.GET.get("option", "")}

    dates = getDates(filters["date"])

    for date in reversed(dates):
        entry = getEntries(date, filters)
        # remove dates with no entries (lessons)
        if (len(entry) == 0):
            dates.remove(date)
            continue

        entries[date] = entry
        weekDays[date] = dateToWeekDay(date)
        weekNumber[date] = dayToWeekNumber(date)

    data = {"dates" : dates, 
            "entries" : entries, 
            "options" : getSelectOptions(filters["sort"]),
            "weekDays" : weekDays,
            "weekNumber" : weekNumber,
            "filters" : filters}

    return render(request, "index.html", context = data)