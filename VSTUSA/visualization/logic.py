from visualization.models import ApiEventholding
from datetime import datetime

def getDates(option : str):
    dates = []

    if (option == "today"):
        dates = ["2024-10-21"]
    elif (option == "tomorrow"):
        dates = ["2024-10-22"]
    elif (option == "this_week"):
        dates = ["2024-10-21", "2024-10-22", "2024-10-23", "2024-10-24", "2024-10-25", "2024-10-26", "2024-10-27"]
    elif (option == "next_week"):
        dates = ["2024-10-28", "2024-10-29", "2024-10-30", "2024-10-31", "2024-11-1", "2024-11-2", "2024-11-3"]

    # remove dates with no lessons
    for d in reversed(dates):
        if (ApiEventholding.objects.filter(date=d).first() == None):
            dates.remove(d)

    return dates

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
    
def dayToWeekNumber(date):
    return "1" if datetime.strptime(date, '%Y-%m-%d').date().isocalendar()[1] % 2 == 1 else "2" 

def getEntries(forDate : str):
    entries = []
    objects = ApiEventholding.objects.filter(date = forDate)

    for obj in objects:
        entry = {}
        
        entry["start_time"] = obj.time_slot.start_time
        entry["end_time"] = obj.time_slot.end_time
        entry["subject"] = obj.event.subject.name
        entry["teacher"] = "TEMP_TEACHER_NAME"
        entry["place_building"] = obj.place.building
        entry["place_room"] = obj.place.room

        entries.append(entry)

    return entries