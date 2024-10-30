from django.shortcuts import render
from django.template.defaulttags import register
from visualization.sqlUsage import *
from datetime import datetime

@register.filter
def getItem(_dict, key):
    _dict
    return _dict.get(key)

def dateToWeekDay(date):
    num = datetime.strptime(date, '%Y-%m-%d').date().weekday()

    if (num == 0):
        return "Понедельник"
    elif (num == 1):
        return "Вторник"
    elif (num == 2):
        return "Среда"
    elif (num == 3):
        return "Четверг"
    elif (num == 4):
        return "Пятница"
    elif (num == 5):
        return "Суббота"
    else:
        return "Воскресение"

def index(request):
    dates = getDates()
    entryToDate = {}
    dayToDate = {}

    for date in dates:
        entryToDate[date] = getEntries(date)
        dayToDate[date] = dateToWeekDay(date)

    data = {"dates" : dates, "entries" : entryToDate, "weekDays" : dayToDate}

    return render(request, "index.html", context = data)