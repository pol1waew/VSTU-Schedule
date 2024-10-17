from django.shortcuts import render
from django.template.defaulttags import register
from visualization.sqlUsage import *

@register.filter
def getItem(_dict, key):
    _dict
    return _dict.get(key)

def index(request):
    dates = getDates()
    entryToDate = {}

    for date in dates:
        entryToDate[date] = getEntries(date)

    data = {"dates" : dates, "entries" : entryToDate}

    return render(request, "index.html", context = data)