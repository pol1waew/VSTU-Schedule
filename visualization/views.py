from api.utilities import ReadAPI
from django.shortcuts import render
from django.template.defaulttags import register
from visualization.logic import *

@register.filter
def list_item(list_, i):
    try:
        return list_[i - 1]
    except:
        return None
    
@register.filter
def is_full_row_canceled(list_, i):
    try:
        if is_same_entries(list_[i - 1], list_[i]):
            return list_[i].is_event_canceled
        return True
    except:
        return True

def index(request):
    selected = {
        "date" : "today", 
        "left_date" : "",
        "right_date" : "",
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

        if "left_date" in request.POST:
            selected["left_date"] = request.POST.get("left_date")
        
        if "right_date" in request.POST:
            selected["right_date"] = request.POST.get("right_date")

        selected["group"] = get_POST_value(request.POST, "group[]")

        selected["teacher"] = get_POST_value(request.POST, "teacher[]")

        selected["place"] = get_POST_value(request.POST, "place[]")

        selected["subject"] = get_POST_value(request.POST, "subject[]")

        selected["kind"] = get_POST_value(request.POST, "kind[]")

        selected["time_slot"] = get_POST_value(request.POST, "time_slot[]")

    # Заменили получение групп/преподавателей:
    # groups = ReadAPI.get_all_groups().values_list("name", flat=True)
    # teachers = ReadAPI.get_all_teachers().values_list("name", flat=True)

    # Берём только тех, кто реально участвует в событиях активных расписаний.
    groups = ReadAPI.get_semester_groups().values_list("name", flat=True)
    teachers = ReadAPI.get_semester_teachers().values_list("name", flat=True)
    
    places = [str(p) for p in ReadAPI.get_all_places()]

    subjects = ReadAPI.get_all_subjects().values_list("name", flat=True)
    kinds = ReadAPI.get_all_kinds().values_list("name", flat=True)
    time_slots = [str(ts) for ts in ReadAPI.get_all_time_slots()]

    data = get_table_data(selected)

    data = {"selected" : selected,
            "groups" : groups,
            "teachers" : teachers,
            "places" : places,

            "subjects" : subjects,
            "kinds" : kinds,
            "time_slots" : time_slots,

            "data" : data,

            "addition_filters_visible" : request.POST.get("addition_filters_visible") if "addition_filters_visible" in request.POST else "0",
            "calendar_visibile" : "1" if "calendar_visibility" in request.POST else "0"
    }
    
    return render(request, "index.html", context = data)
