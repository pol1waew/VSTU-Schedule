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
    context = {}

    if request.method == "POST":
        selected = {}

        if "date" in request.POST:
            selected["date"] = request.POST.get("date")
        else:
            selected["date"] = "today"

        if "left_date" in request.POST:
            selected["left_date"] = request.POST.get("left_date")
        else:
            selected["left_date"] = ""
        
        if "right_date" in request.POST:
            selected["right_date"] = request.POST.get("right_date")
        else:
            selected["right_date"] = ""

        selected["group"] = get_POST_value(request.POST, "group[]")
        selected["teacher"] = get_POST_value(request.POST, "teacher[]")
        selected["place"] = get_POST_value(request.POST, "place[]")
        selected["subject"] = get_POST_value(request.POST, "subject[]")
        selected["kind"] = get_POST_value(request.POST, "kind[]")
        selected["time_slot"] = get_POST_value(request.POST, "time_slot[]")

        context["selected"] = selected
        context["data"] = get_table_data(selected)

        context["groups"] = ReadAPI.get_all_groups().values_list("name", flat=True)
        context["teachers"] = ReadAPI.get_all_teachers().values_list("name", flat=True)
        context["places"] = [str(p) for p in ReadAPI.get_all_places()]
        context["subjects"] = ReadAPI.get_all_subjects().values_list("name", flat=True)
        context["kinds"] = ReadAPI.get_all_kinds().values_list("name", flat=True)
        context["time_slots"] = [str(ts) for ts in ReadAPI.get_all_time_slots()]

        context["addition_filters_visible"] = request.POST.get("addition_filters_visible") if "addition_filters_visible" in request.POST else "0"
        context["calendar_visibile"] = "1" if "calendar_visibility" in request.POST else "0"

    return render(request, "index.html", context=context)
