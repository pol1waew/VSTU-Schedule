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

    filters = {"date" : 2,
               "sort" : 0}

    if (request.GET.get("today", False)):
        filters["date"] = 0
        dates = getDates("today")
    elif (request.GET.get("tomorrow", False)):
        filters["date"] = 1
        dates = getDates("tomorrow")
    elif (request.GET.get("next_week", False)):
        filters["date"] = 3
        dates = getDates("next_week")
    else:
        filters["date"] = 2
        dates = getDates("this_week")

    for date in dates:
        entries[date] = getEntries(date)
        weekDays[date] = dateToWeekDay(date)
        weekNumber[date] = dayToWeekNumber(date)

    data = {"dates" : dates, 
            "entries" : entries, 
            "weekDays" : weekDays,
            "weekNumber" : weekNumber,
            "filters" : filters}

    return render(request, "index.html", context = data)