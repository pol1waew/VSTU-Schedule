from api.utilities import ReadAPI
from django.shortcuts import render
from django.template.defaulttags import register
from datetime import datetime
from visualization.logic import *

@register.filter
def list_item(list_, i):
    try:
        return list_[i - 1]
    except:
        return None

@register.filter
def dateFormat(date):
    return datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")


def index(request):
    selected = {
        "date" : "today", 
        "group" : "", 
        "teacher" : "",
        "place" : "",
        "subject" : "",
        "kind" : "",
        "time_slot" : ""
    }

    if request.method == "POST":
        if "date" in request.POST:
            selected["date"] = request.POST.get("date")

        if "group[]" in request.POST:
            selected["group"] = request.POST.getlist("group[]") 
        
        if "teacher[]" in request.POST:
            selected["teacher"] = request.POST.getlist("teacher[]")
            if type(selected["teacher"]) is list and len(selected["teacher"]) == 1:
                selected["teacher"] = selected["teacher"][0]

        if "place[]" in request.POST:
            selected["place"] = request.POST.getlist("place[]") 

        if "subject[]" in request.POST:
            selected["subject"] = request.POST.getlist("subject[]") 

        if "kind[]" in request.POST:
            selected["kind"] = request.POST.getlist("kind[]") 
            
        if "time_slot[]" in request.POST:
            selected["time_slot"] = request.POST.getlist("time_slot[]") 


    groups = ReadAPI.get_all_groups().values_list("name", flat=True)
    teachers = ReadAPI.get_all_teachers().values_list("name", flat=True)
    places = [str(p) for p in ReadAPI.get_all_places()]

    subjects = ReadAPI.get_all_subjects().values_list("name", flat=True)
    kinds = ReadAPI.get_all_kinds().values_list("name", flat=True)
    time_slots = [str(ts) for ts in ReadAPI.get_all_time_slots()]

    entries = get_table_data(selected)
    print(entries)

    data = {"selected" : selected,
            "groups" : groups,
            "teachers" : teachers,
            "places" : places,

            "subjects" : subjects,
            "kinds" : kinds,
            "time_slots" : time_slots,

            "entries" : entries,

            "addition_filters_visible" : request.POST.get("addition_filters_visible") if "addition_filters_visible" in request.POST else "0"
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
        entry = get_table_data(date, filters)
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