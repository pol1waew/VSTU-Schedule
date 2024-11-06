from api.models import EventHolding, EventParticipant, EventPlace
from datetime import datetime

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

def getEntries(forDate : str, filters):
    entries = []
    holdings = EventHolding.objects.filter(date = forDate)
    
    if (filters["option"] == ""):
        holdings = EventHolding.objects.filter(date = forDate)
    else:
        if (filters["sort"] == 0 or filters["sort"] == 1):
            holdings = EventHolding.objects.filter(date = forDate, event__participants__name = filters["option"])
        else:
            holdings = EventHolding.objects.filter(date = forDate, 
                                                   place__building = filters["option"].split(" ", 1)[0], 
                                                   place__room = filters["option"].split(" ", 1)[1])        

    for hold in holdings:
        entry = {}
        
        entry["start_time"] = hold.time_slot.start_time
        entry["end_time"] = hold.time_slot.end_time
        entry["subject"] = hold.event.subject.name
        if (filters["sort"] == 0 or filters["sort"] == 2):
            participants = EventParticipant.objects.filter(event = hold.event, role = "teacher")
            for p in participants:
                entry["teacher"] = p.name
        if (filters["sort"] == 1 or filters["sort"] == 2):
            participants = EventParticipant.objects.filter(event = hold.event, role = "student")
            for p in participants:
                entry["group"] = p.name
        if (not filters["sort"] == 2):
            entry["place_building"] = hold.place.building
            entry["place_room"] = hold.place.room

        entries.append(entry)

    return entries

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