from django.shortcuts import render
from django.template.defaulttags import register
from datetime import datetime
from visualization.logic import *

@register.filter
def getItem(_dict, key):
    _dict
    return _dict.get(key)

@register.filter
def dateFormat(date):
    return datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")


def index(request):
    data = {"dates" : [], 
            "entries" : {}, 
            "calendar" : {},
            "options" : [],
            "weekDays" : {},
            "weekNumber" : {},
            "filters" : {"date" : 2, "sort" : 0, "option" : ""}
    }
    
    return render(request, "index.html", context = data)

    dates = []
    entries = {}
    calendar = {}
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
        calendar[date] = getCalendar(date)
        weekDays[date] = dateToWeekDay(date)
        weekNumber[date] = dayToWeekNumber(date)

    data = {"dates" : dates, 
            "entries" : entries, 
            "calendar" : calendar,
            "options" : getSelectOptions(filters["sort"]),
            "weekDays" : weekDays,
            "weekNumber" : weekNumber,
            "filters" : filters}

    return render(request, "index.html", context = data)